# -*- coding: utf-8 -*-


from engine.datasource.adi import Adi
from engine.datasource.artigos import Artigos
from engine.datasource.cisi import Cisi
from engine.datasource.cran import Cran
from engine.datasource.lisa import Lisa
from engine.datasource.medline import Medline
from engine.datasource.npl import NPL
from engine.datasource.timed import Timed
from engine.query import QueryProcessor
from gensim.models import Word2Vec
from gensim.models import KeyedVectors

import logging
import os



script_dir = os.path.dirname(__file__)
ROOT_PROJ = os.path.join(script_dir, '../../')
source_path = os.path.join(script_dir, 'data/med/')


source_list = [Medline(path=ROOT_PROJ+'data/med/')]#,Cran(path=ROOT_PROJ+'data/cran/'),Adi(path=ROOT_PROJ+'data/adi/'),Timed(path=ROOT_PROJ+'data/time/'),Cisi(path=ROOT_PROJ+'data/cisi/'),Medline(path=ROOT_PROJ+'data/med/'),NPL(path=ROOT_PROJ+'data/npl/'),Lisa(path=ROOT_PROJ+'data/lisa/'),Artigos(path=ROOT_PROJ+'data/artigos/')]

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

window_l = [5]#,5,10,20]
size_l = [300]#50,100,300]


for source in source_list:
    for w in window_l:
        for s in size_l:
            print(source.path + source.info+('%s_%s.model'%(w,s)))
            print('Source '+source.info)
            preprocess = source.preprocessor
            preprocess.expand_terms = True

            print('Representation Docs')
            index = preprocess.get_representation_docs()

            query_processor = QueryProcessor(preprocessor=preprocess,reduce=True)
            print('Representation Querys')
            querys = preprocess.get_representation_query()

            print("Index size %d" % len(index.index))
            print("Matrix size %s" % index.matrix.getnnz())

            sentences = []

            for doc in source.read_docs():
                sentences.append(preprocess.tokenize(doc.text))

            model = Word2Vec(sentences, window=w, size=s, workers=4,min_count=2)

            model.wv.save(source.path + source.info+('%s_%s.model'%(w,s)))
            model.wv.save_word2vec_format(source.path + source.info+('%s_%s.model.bin'%(w,s)), binary=True)

    #model1 = KeyedVectors.load_word2vec_format(source.path + source.info+'.model.bin', binary=True)




