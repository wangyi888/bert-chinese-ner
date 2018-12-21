# coding:utf-8
'''
author:wangyi
'''
import tornado.web
from tornado.options import define, options
import os
from utils import get_entity

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class ResultHandler(tornado.web.RequestHandler):

    def post(self):
        content = self.get_argument('content').strip()
        type = self.get_argument('type').strip()
        demo_sent = list(content)
        predict_in = open('./data/test_predict.txt','w',encoding='utf-8')
        for word in content:
            predict_in.write(word+'\t'+'O'+'\n')
            predict_in.flush()
        print('predict input_file created!')
        command = 'CUDA_VISIBLE_DEVICES="3" ' \
                  'python BERT_NER.py --data_dir=data/ ' \
                  '--bert_config_file=checkpoint/bert_config.json ' \
                  '--init_checkpoint=checkpoint/model.ckpt-1000000 --vocab_file=vocab.txt ' \
                  '--output_dir=./output/result_dir/ --do_train=False --do_predict=True'
        print(command)
        os.system(command)
        print('predict result_file is created!')
        tag = []
        with open('./output/result_dir/label_test.txt',encoding='utf-8') as f:
            for line in f.readlines():
                if line.strip()!='[CLS]' and line.strip()!='[SEP]':
                    tag.append(line.strip())
        result = get_entity(tag, demo_sent,all_class)
        res = []
        for any_class in all_class:
            m = {}
            if len(result[any_class]) > 0:
                m['label'] = any_class
                m['content'] = list(set(result[any_class]))
                res.append(m)
        self.render('result.html',content=content,result=res,type=type)


if __name__ == '__main__':

    define("port", default=9096, help="run on the given port", type=int)
    all_class = ['盗窃文物', '偷拿家庭成员或者近亲属的财物，追究刑事责任的',
                 '采用破坏性手段盗窃古文化遗址、古墓葬以外的（古建筑、石窟寺、石刻、壁画、近代现代重要史迹和代表性建筑等）其他不可移动文物',
                 '盗窃罪-共犯', '将国家、集体、他人所有并已经伐倒的树木窃为己有', '数额较大', '多次盗窃', '数额巨大', '邮政工作人员窃取邮件财物',
                 '公私财物', '采用破坏性手段盗窃公私财物，造成其他财物损毁', '以非法占有为目的', '盗窃数额提取', '未成年人盗窃未遂或中止', '数额特别巨大',
                 '未成年人盗窃数额较大，未超过三次，如实供述积极退赃，具有其他轻微情节', '入户盗窃', '偷拿家庭成员或近亲属财物，获得谅解',
                 '盗窃油气或者正在使用的油气设备，构成犯罪，但未危害公共安全', '金额_盗窃金额', '未成年人盗窃自己家庭或者近亲属财物', '偷砍他人房前屋后、自留地种植的零星树木',
                 '一般盗窃行为', '秘密窃取', '以牟利为目的，盗接他人通信线路、复制他人电信码号', '携带凶器盗窃', '盗窃数额较大，行为人认罪悔罪，退赃退赔，被害人谅解，情节轻微',
                 '采用破坏性手段盗窃古文化遗址、古墓葬以外的（古建筑、石窟寺、石刻、壁画、近代现>代重要史迹和代表性建筑等）其他不可移动文物',
                 '未成年人起次要或辅助作用，或被胁迫盗窃数额较大，未超过三次，如实供述积极退赃', '其他严重情节', '盗窃信用卡并使用', '扒窃']
    app = tornado.web.Application(
        handlers=[(r'/', IndexHandler), (r'/result/show', ResultHandler)],
        template_path=os.path.join(os.path.dirname(__file__), "templates"), debug=True
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()