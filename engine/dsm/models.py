# # -*- coding: utf-8 -*-
#
#
# #nltk.download()
# from django_extensions.settings import BASE_DIR
#
# from engine.datasource.adi import Adi
# from engine.datasource.artigos import Artigos
# from engine.datasource.cisi import Cisi
# from engine.datasource.cran import Cran
# from engine.datasource.lisa import Lisa
# from engine.datasource.medline import Medline
# from engine.datasource.npl import NPL
# from engine.datasource.timed import Timed
# from engine.query import QueryProcessor
# from gensim.models import Word2Vec
# from gensim.models import KeyedVectors
#
# import logging
#
# ROOT_PROJ = BASE_DIR
#
# source_list = [NPL(path=ROOT_PROJ+'data/npl/')]
# #[Cran(path=ROOT_PROJ+'data/cran/'),Adi(path=ROOT_PROJ+'data/adi/'),Timed(path=ROOT_PROJ+'data/time/'),Cisi(path=ROOT_PROJ+'data/cisi/')]#[Medline(path=ROOT_PROJ+'data/med/'),NPL(path=ROOT_PROJ+'data/npl/'),Lisa(path=ROOT_PROJ+'data/lisa/'),Artigos(path=ROOT_PROJ+'data/artigos/')]
#
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
#
# for source in source_list:
#
#     print('Source '+source.info)
#     preprocess = source.preprocessor
#
#     print('Representation Docs')
#     index = preprocess.get_representation_docs()
#
#     query_processor = QueryProcessor(preprocessor=preprocess,reduce=True)
#     print('Representation Querys')
#     querys = preprocess.get_representation_query()
#
#     print("Index size %d" % len(index.index))
#     print("Matrix size %s" % index.matrix.getnnz())
#
#     sentences = []
#
#     for doc in source.read_docs():
#         sentences.append(preprocess.tokenize(doc.text))
#
#     model = Word2Vec(sentences, size=300, workers=5, window=10)
#
#     model.wv.save(source.path+ source.info+'.model')
#     model.wv.save_word2vec_format(source.path + source.info+'.model.bin', binary=True)
#
#     #model1 = KeyedVectors.load_word2vec_format(source.path + source.info+'.model.bin', binary=True)
#
#
#
#
