import os
from collections import defaultdict

import numpy as np
import matplotlib
import re
import matplotlib.pyplot as plt
from itertools import cycle

from engine.datasource.adi import Adi
from engine.datasource.cisi import Cisi
from engine.datasource.cran import Cran
from engine.datasource.lisa import Lisa
from engine.datasource.npl import NPL
from engine.datasource.timed import Timed
from engine.queryexpansion.analysis_context import AnalysisContextLocal, AnalysisContextLocalDSM, \
    AnalysisContextLocalDSMGlobal
from engine.util import get_class
from engine.core import Engine
from engine.datasource.medline import Medline
from engine.eval import EvaluationResult
from engine.query import QueryProcessor, WordnetQueryProcess

#matplotlib.use('Agg')

TREC_EVAL_COMMAND = "/usr/local/bin/trec_eval -q -c %s %s"
fig, ax = plt.subplots()

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)



def plot_topi_ap(eval_result,outfile,sort_on_AP = False):
    r = eval_result
    topic_names = natural_sort(r.queries.keys())
    AP = np.array([r.queries[q]["map"] for q in topic_names])
    ylabel = "Average Precision"

    if sort_on_AP:
        topic_names = [n for (d, n) in sorted(zip(AP, topic_names), reverse=True)]
        AP = sorted(AP, reverse=True)

    ind = np.arange(len(topic_names))
    width = 1.0
    rects = plt.bar(ind, AP, width)
    plt.xticks(ind + 0.5 * width, topic_names, fontsize=10, rotation='vertical')
    plt.ylabel(ylabel)
    plt.xlabel("Topic")

    plt.savefig(outfile, bbox_inches='tight')
    plt.close()

colors = ['navy', 'turquoise', 'darkorange', 'cornflowerblue', 'teal','sienna','violet', 'green', 'red', 'yellow', 'black', 'blue', 'gray',
         'orange', 'pink']

markers = ["s","o","v","^","<",">","p","P","*","x","D","+","X","d","3"]
def plot_pr_curve(eval_result, name , lines, labels,id):

    #name = eval_result.runid
    r = eval_result
    iprec = [r.results["iprec_at_recall_0.00"],
              r.results["iprec_at_recall_0.10"],
              r.results["iprec_at_recall_0.20"],
              r.results["iprec_at_recall_0.30"],
              r.results["iprec_at_recall_0.40"],
              r.results["iprec_at_recall_0.50"],
              r.results["iprec_at_recall_0.60"],
              r.results["iprec_at_recall_0.70"],
              r.results["iprec_at_recall_0.80"],
              r.results["iprec_at_recall_0.90"],
              r.results["iprec_at_recall_1.00"]]

    recall = np.arange(0, 1.1, 0.1)

    l, = plt.plot(recall, iprec, '-', color=colors[id], lw=1)
    l, = plt.plot(recall, iprec, markers[id], color=colors[id], lw=2)

    lst = name.split('_')

    lines.append(l)
    labels.append('%s-%s' % (lst[1], lst[3]))

def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')

def plot_bar_stat(dic_stat, labels, outfile,metrics, title):
    N = len(metrics)
    print(labels)
    ind = np.arange(N)  # the x locations for the groups
    width = 0.07  # the width of the bars

    fig, ax = plt.subplots()
    fig.set_size_inches(8, 6)

    rects = []
    for i,l in enumerate(labels):
         m_metric = dic_stat[l]
         rects.append(ax.bar(ind + width*i, m_metric, width, color=colors[i]))


    # add some text for labels, title and axes ticks
    ax.set_ylabel('Scores')
    ax.set_title(title+': Scores by Metrics and Algorithm')
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(metrics)

    ax.legend(rects, labels,prop=dict(size=8))

    [autolabel(r) for r in rects]

    plt.savefig(outfile, bbox_inches='tight')




if __name__ == '__main__':
    path_retrieval_file = '/tmp/%s.RET'
    path_relevant_file = '/tmp/%s.REL'
    path_result_file = '/tmp/%s.RES'
    path_pr_curve_file = '/tmp/%s.png'
    path_source = '/Users/fabiano/Dropbox/Mestrado/UECE/DISSERTACAO/SISTEMA/luppar/data/npl/'

    lines = []
    labels = []
    plt.figure(figsize=(9, 7))
    dic_stat = defaultdict(list)
    metrics = ['map', 'bpref', 'recip_rank']

    #'engine.search.BM25Search',
    cf_model = ['engine.search.BM25Search']
    cf_mode = ['or'] #,'nor']
    cf_reduce = [True]#, True]
    print('Source')
    source = NPL(path=path_source)
    source.read_docs()
    print('Preprocess')
    preprocess = source.preprocessor
    avg_size = preprocess.get_representation_docs().avg_size

    #WordnetQueryProcess(preprocessor=preprocess),AnalysisContextLocal(preprocessor=preprocess),
    cf_expanded = [QueryProcessor(preprocessor=preprocess),WordnetQueryProcess(preprocessor=preprocess),AnalysisContextLocal(preprocessor=preprocess),AnalysisContextLocalDSM(preprocessor=preprocess)]
    iii=0
    for cft in cf_model:
        for cfm in cf_mode:
            for cfe in cf_expanded:
                for cfr in cf_reduce:
                    #GenericPreprocessor(source=fonte)
                    print('Representation Docs')
                    index = preprocess.get_representation_docs()
                    query_processor = cfe
                    print('Representation Querys')
                    querys = preprocess.get_representation_query()

                    params = {'mode': cfm}
                    search_model = get_class(cft)(params=params)#BM25Search(params=params)
                    search_model.set_index(index)
                    print('Setting Engine')
                    engine = Engine(source, query_processor, search_model, free_search=False)


                    fo_rel = open(path_relevant_file % engine.slug(), 'wt')
                    fo_ret  = open(path_retrieval_file % engine.slug(), 'wt')
                    z=0
                    for q in list(source.read_querys()):
                        print('Read query %s' % q.id)
                        z+=1

                        #profile.run('query_result = engine.search(q.text, qid=q.id);print()')
                        query_result = engine.search(q.text, qid=q.id)

                        #Problema TODO UID x ID
                        docs_list_retrieval = [engine.index.get_doc_item(d).id for d in query_result.docs_retrieval]
                        docs_list_relevant = [d for d in query_result.docs_relevant]
                        docs_score_relevant = [v for v in query_result.docs_scores]

                        print('Write out...')

                        for i, d in enumerate(docs_list_relevant):
                            fo_rel.write('%d 0 %s %d\n' % (q.id, d, 1))

                        for i,(d,s) in enumerate(zip(docs_list_retrieval,docs_score_relevant)):
                            fo_ret.write('%d Q0 %s %d %f %s\n' % (q.id, d, i, s,source.info))

                    fo_rel.close()
                    fo_ret.close()

                    output = os.popen(TREC_EVAL_COMMAND % (path_relevant_file % engine.slug(), path_retrieval_file % engine.slug()))
                    fo = open(path_result_file % engine.slug(), 'wt')

                    for linha in output:
                       fo.write(linha)
                    fo.close()

                    print(engine.slug())
                    ev = EvaluationResult(path_result_file % engine.slug())
                    ev.print_summary_statistic()


                    plot_pr_curve(ev,name=engine.slug(), lines = lines, labels=labels,id=iii)
                    for m in metrics:
                       dic_stat[labels[iii]].append(ev.results[m])

                    iii+=1
                    #plot_topi_ap(ev, path_pr_curve_file % (engine.slug()+"_TOPIC"))

    outfile = path_pr_curve_file % (source.info + "_PR")
    outfile2 = path_pr_curve_file % (source.info + "_MT")

    fig = plt.gcf()
    fig.subplots_adjust(bottom=0.25)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("Recall")
    plt.ylabel("Interpolated Precision")
    plt.title(source.info +': Precision-Recall')

    plt.legend(lines, labels, prop=dict(size=8))
    plt.savefig(outfile, bbox_inches='tight')
    plt.close()

    plot_bar_stat(dic_stat, labels, outfile2,metrics, source.info)

    #TODO
    #Verificar a ordem das metricas algo estranho
    # print "Search query: %s" % (query_result.text)
    # print "Query vector: %s" % (query_result.query_vector)
    # print "Total documents retrieval %d" % (len(docs_list_retrieval))
    # print "Total documents relevant %d" % (len(docs_list_relevant))


