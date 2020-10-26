from axon.db.recorder import WaveFrontRecorder, SqlDbRecorder, \
    ElasticSearchRecorder
from axon.common import config as conf
from axon.common import consts


class RecorderFactory(object):

    @classmethod
    def get_recorders(cls):
        def get_wf_recorder():
            if conf.WAVEFRONT_PROXY_ADDRESS is not None:
                server = conf.WAVEFRONT_PROXY_ADDRESS
                proxy = True
                token = None
            else:
                server = conf.WAVEFRONT_SERVER_ADDRESS
                proxy = False
                token = conf.WAVEFRONT_SERVER_API_TOKEN
            return WaveFrontRecorder(server, proxy, token)

        def get_es_recorder():
            if conf.ELASTIC_SEARCH_SERVER_ADDRESS:
                server = conf.ELASTIC_SEARCH_SERVER_ADDRESS
                port = conf.ELASTIC_SEARCH_SERVER_PORT
                return ElasticSearchRecorder(server, port)


        if not conf.RECORDER:   # no recorder specified
            return [SqlDbRecorder()]

        recorders = [x.lower() for x in conf.RECORDER.split(",")]
        recs = []

        if consts.WAVEFRONT in recorders:
            recs.append(get_wf_recorder())

        if consts.SQL in recorders:
            recs.append(SqlDbRecorder())

        if consts.ELASTIC_SEARCH in recorders:
            recs.append(get_es_recorder())

        return recs
