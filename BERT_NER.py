#! usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Copyright 2018 The Google AI Language Team Authors.
BASED ON Google_BERT.
@Author:zhoukaiyin
Adjust code for chinese ner
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import os
from bert import modeling
from bert import optimization
from bert import tokenization
import tensorflow as tf
from tensorflow.contrib.crf import crf_log_likelihood,crf_decode
from sklearn.metrics import f1_score,precision_score,recall_score
from tensorflow.python.ops import math_ops
import tf_metrics
import pickle
flags = tf.flags

FLAGS = flags.FLAGS

flags.DEFINE_string(
    "data_dir", None,
    "The input datadir.",
)

flags.DEFINE_string(
    "bert_config_file", None,
    "The config json file corresponding to the pre-trained BERT model."
)

flags.DEFINE_string(
    "task_name", "NER", "The name of the task to train."
)

flags.DEFINE_string(
    "output_dir", None,
    "The output directory where the model checkpoints will be written."
)

## Other parameters
flags.DEFINE_string(
    "init_checkpoint", None,
    "Initial checkpoint (usually from a pre-trained BERT model)."
)

flags.DEFINE_bool(
    "do_lower_case", True,
    "Whether to lower case the input text."
)

flags.DEFINE_integer(
    "max_seq_length", 512,
    "The maximum total input sequence length after WordPiece tokenization."
)

flags.DEFINE_bool(
    "do_train", True,
    "Whether to run training."
)
flags.DEFINE_bool("use_tpu", False, "Whether to use TPU or GPU/CPU.")

flags.DEFINE_bool("do_eval", False, "Whether to run eval on the dev set.")

flags.DEFINE_bool("do_predict", False,"Whether to run the model in inference mode on the test set.")

flags.DEFINE_integer("train_batch_size", 6, "Total batch size for training.")

flags.DEFINE_integer("eval_batch_size", 8, "Total batch size for eval.")

flags.DEFINE_integer("predict_batch_size", 8, "Total batch size for predict.")

flags.DEFINE_float("learning_rate", 5e-5, "The initial learning rate for Adam.")

flags.DEFINE_float("num_train_epochs", 40.0, "Total number of training epochs to perform.")



flags.DEFINE_float(
    "warmup_proportion", 0.1,
    "Proportion of training to perform linear learning rate warmup for. "
    "E.g., 0.1 = 10% of training.")

flags.DEFINE_integer("save_checkpoints_steps", 1000,
                     "How often to save the model checkpoint.")

flags.DEFINE_integer("iterations_per_loop", 1000,
                     "How many steps to make in each estimator call.")

flags.DEFINE_string("vocab_file", None,
                    "The vocabulary file that the BERT model was trained on.")
tf.flags.DEFINE_string("master", None, "[Optional] TensorFlow master URL.")
flags.DEFINE_integer(
    "num_tpu_cores", 8,
    "Only used if `use_tpu` is True. Total number of TPU cores to use.")

class InputExample(object):
    """A single training/test example for simple sequence classification."""

    def __init__(self, guid, text, label=None):
        """Constructs a InputExample.

        Args:
          guid: Unique id for the example.
          text_a: string. The untokenized text of the first sequence. For single
            sequence tasks, only this sequence must be specified.
          label: (Optional) string. The label of the example. This should be
            specified for train and dev examples, but not for test examples.
        """
        self.guid = guid
        self.text = text
        self.label = label


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self, input_ids, input_mask, segment_ids, label_ids,):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_ids = label_ids
        #self.label_mask = label_mask


class DataProcessor(object):
    """Base class for data converters for sequence classification data sets."""

    def get_train_examples(self, data_dir):
        """Gets a collection of `InputExample`s for the train set."""
        raise NotImplementedError()

    def get_dev_examples(self, data_dir):
        """Gets a collection of `InputExample`s for the dev set."""
        raise NotImplementedError()

    def get_labels(self):
        """Gets the list of labels for this data set."""
        raise NotImplementedError()

    @classmethod
    def _read_data(cls, input_file):
        """Reads a BIO data."""
        with open(input_file) as f:
            lines = []
            words = []
            labels = []
            for line in f:
                contends = line.strip()
                #print('contends',contends)
                word = line.strip().split('\t')[0]
                label = line.strip().split('\t')[-1]
                #print('label',label)
                if contends.startswith("-DOCSTART-"):
                    words.append('')
                    continue
                #print('-1:',words[-1])
                if len(contends) == 0 and words[-1] == '。':
                    #print('进来了吗')
                    l = ' '.join([label for label in labels if len(label) > 0])
                    w = ' '.join([word for word in words if len(word) > 0])
                    lines.append([l, w])
                    words = []
                    labels = []
                    continue
                words.append(word)
                labels.append(label)
            #print('-1:',words[-1])
            #print('lines',lines)
            return lines


class NerProcessor(DataProcessor):
    def get_train_examples(self, data_dir):
        return self._create_example(
            self._read_data(os.path.join(data_dir, "train.txt")), "train"
        )

    def get_dev_examples(self, data_dir):
        return self._create_example(
            self._read_data(os.path.join(data_dir, "test.txt")), "dev"
        )

    def get_test_examples(self,data_dir):
        return self._create_example(
            self._read_data(os.path.join(data_dir, "test.txt")), "test")


    def get_labels(self):
        '''
        label_dir = os.path.join(FLAGS.data_dir,'labels.pkl')
        if not os.path.exists(label_dir):
            labels = []
            folder = os.listdir(FLAGS.data_dir)
            for file in folder:
                with open(os.path.join(FLAGS.data_dir,file),encoding='utf-8') as f:
                    for i,line in enumerate(f.readlines()):
                        if len(line.split('\t')) > 1:
                            label = line.split('\t')[1].strip()
                            if label not in labels:
                                labels.append(label)
            labels.append("X")
            labels.append("[CLS]")
            labels.append("[SEP]")
            pickle.dump(labels,open(label_dir,'wb'))
        else:
            labels = pickle.load(open(label_dir,'rb'))
        print('labels:',labels,'len(labels):',len(labels))
        return labels
        '''
        #return ["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "X","[CLS]","[SEP]"]
        return ['I-盗窃文物', 'I-扒窃', 'I-未成年人起次要或辅助作用，或被胁迫盗窃数额较大，未超过三次，如实供述积极退赃', 'B-偷砍他人房前屋后、自留地种植的零星树木', 'B-携带凶器盗窃', 'B-将国家、集体、他人所有并已经伐倒的树木窃为己有', '[CLS]', 'B-公私财物', 'I-采用破坏性手段盗窃古文化遗址、古墓葬以外的（古建筑、石窟寺、石刻、壁画、近代现>代重要史迹和代表性建筑等）其他不可移动文物', 'I-偷拿家庭成员或近亲属财物，获得谅解', 'B-未成年人盗窃数额较大，未超过三次，如实供述积极退赃，具有其他轻微情节', 'I-采用破坏性手段盗窃古文化遗址、古墓葬以外的（古建筑、石窟寺、石刻、壁画、近代现代重要史迹和代表性建筑等）其他不可移动文物', 'B-以牟利为目的，盗接他人通信线路、复制他人电信码号', 'B-盗窃罪-共犯', 'B-数额特别巨大', 'X', 'B-盗窃油气或者正在使用的油气设备，构成犯罪，但未危害公共安全', 'B-盗窃文物', 'I-盗窃信用卡并使用', 'I-数额特别巨大', 'B-数额较大', 'O', 'B-盗窃数额较大，行为人认罪悔罪，退赃退赔，被害人谅解，情节轻微', 'B-偷拿家庭成员或近亲属财物，获得谅解', 'I-未成年人盗窃未遂或中止', 'B-邮政工作人员窃取邮件财物', 'I-携带凶器盗窃', 'B-数额巨大', 'B-未成年人起次要或辅助作用，或被胁迫盗窃数额较大，未超过三次，如实供述积极退赃', 'B-采用破坏性手段盗窃公私财物，造成其他财物损毁', '[SEP]', 'I-盗窃数额较大，行为人认罪悔罪，退赃退赔，被害人谅解，情节轻微', 'B-盗窃数额提取', 'B-扒窃', 'I-未成年人盗窃自己家庭或者近亲属财物', 'B-采用破坏性手段盗窃古文化遗址、古墓葬以外的（古建筑、石窟寺、石刻、壁画、近代现代重要史迹和代表性建筑等）其他不可移动文物', 'I-金额_盗窃金额', 'B-以非法占有为目的', 'I-邮政工作人员窃取邮件财物', 'I-以牟利为目的，盗接他人通信线路、复制他人电信码号', 'B-其他严重情节', 'B-多次盗窃', 'B-秘密窃取', 'I-以非法占有为目的', 'I-采用破坏性手段盗窃公私财物，造成其他财物损毁', 'I-盗窃罪-共犯', 'I-盗窃油气或者正在使用的油气设备，构成犯罪，但未危害公共安全', 'B-未成年人盗窃未遂或中止', 'I-未成年人盗窃数额较大，未超过三次，如实供述积极退赃，具有其他轻微情节', 'I-偷拿家庭成员或者近亲属的财物，追究刑事责任的', 'B-盗窃信用卡并使用', 'I-公私财物', 'I-数额巨大', 'I-偷砍他人房前屋后、自留地种植的零星树木', 'I-多次盗窃', 'B-未成年人盗窃自己家庭或者近亲属财物', 'B-偷拿家庭成员或者近亲属的财物，追究刑事责任的', 'I-入户盗窃', 'I-秘密窃取', 'I-其他严重情节', 'B-入户盗窃', 'I-盗窃数额提取', 'I-将国家、集体、他人所有并已经伐倒的树木窃为己有', 'I-数额较大', 'I-一般盗窃行为', 'B-金额_盗窃金额', 'B-一般盗窃行为']

        #return ['O', 'B-未取得医生执业资格的人非法行医', 'I-未取得医生执业资格的人非法行医',
        #         'B-未取得或以非法手段取得医师资格从事医疗活动', 'I-未取得或以非法手段取得医师资格从事医疗活动',
        #         'B-情节严重', 'I-情节严重', 'B-未取得乡村医生执业证书，从事乡村医疗活动', 'I-未取得乡村医生执业证书，从事乡村医疗活动',
        #         'B-造成就诊人死亡', 'I-造成就诊人死亡', 'B-以营利为目的', 'I-以营利为目的', 'B-未经著作权人许可，复制发行他人作品', 'I-未经著作权人许可，复制发行他人作品',
        #         'B-作品', 'I-作品', 'B-其他特别严重情节', 'I-其他特别严重情节', 'B-其他严重情节', 'I-其他严重情节', 'B-侵犯著作权罪-共犯', 'I-侵犯著作权罪-共犯',
        #         'B-制作、出售假冒他人署名的美术作品', 'I-制作、出售假冒他人署名的美术作品', 'B-假冒他人署名的美术作品', 'I-假冒他人署名的美术作品',
        #         'B-犯侵犯著作权罪，又销售该侵权复制品', 'I-犯侵犯著作权罪，又销售该侵权复制品', 'B-录音录像制品', 'I-录音录像制品',
        #         'B-未经录音录像制作者许可，复制发行其制作的录音录像制品', 'I-未经录音录像制作者许可，复制发行其制作的录音录像制品',
        #         'B-出版他人享有专有出版权的图书', 'I-出版他人享有专有出版权的图书', 'B-他人享有专有出版权的图书', 'I-他人享有专有出版权的图书',
        #         'B-数额巨大', 'I-数额巨大', 'B-二年内多次容留他人吸毒', 'I-二年内多次容留他人吸毒', 'B-毒品', 'I-毒品', 'B-毒品再犯', 'I-毒品再犯',
        #         'B-一次容留多人吸毒', 'I-一次容留多人吸毒', 'B-容留他人吸毒造成严重后果', 'I-容留他人吸毒造成严重后果', 'B-容留未成年人吸毒', 'I-容留未成年人吸毒',
        #         'B-二年内曾因容留他人吸毒受过行政处罚', 'I-二年内曾因容留他人吸毒受过行政处罚', 'B-严重损害就诊人身体健康', 'I-严重损害就诊人身体健康',
        #         'B-数额较大', 'I-数额较大', 'B-侵犯著作权罪-单位', 'I-侵犯著作权罪-单位', 'B-以牟利为目的容留他人吸毒', 'I-以牟利为目的容留他人吸毒',
        #         'B-利用教唆特定人员进行毒品犯罪', 'I-利用教唆特定人员进行毒品犯罪',"X","[CLS]","[SEP]"]


    def _create_example(self, lines, set_type):
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            text = tokenization.convert_to_unicode(line[1])
            label = tokenization.convert_to_unicode(line[0])
            examples.append(InputExample(guid=guid, text=text, label=label))
        return examples


def write_tokens(tokens,mode):
    if mode=="test":
        path = os.path.join(FLAGS.output_dir, "token_"+mode+".txt")
        wf = open(path,'a')
        for token in tokens:
            if token!="**NULL**":
                wf.write(token+'\n')
        wf.close()

def convert_single_example(ex_index, example, label_list, max_seq_length, tokenizer,mode):
    label_map = {}
    for (i, label) in enumerate(label_list,1):
        label_map[label] = i
    with open(os.path.join(FLAGS.output_dir,'label2id.pkl'),'wb') as w:
        pickle.dump(label_map,w)
    textlist = example.text.split(' ')
    labellist = example.label.split(' ')
    tokens = []
    labels = []
    # print(textlist)
    for i, word in enumerate(textlist):
        token = tokenizer.tokenize(word)
        # print(token)
        tokens.extend(token)
        label_1 = labellist[i]
        # print(label_1)
        for m in range(len(token)):
            if m == 0:
                labels.append(label_1)
            else:
                labels.append("X")
        # print(tokens, labels)
    # tokens = tokenizer.tokenize(example.text)
    if len(tokens) >= max_seq_length - 1:
        tokens = tokens[0:(max_seq_length - 2)]
        labels = labels[0:(max_seq_length - 2)]
    ntokens = []
    segment_ids = []
    label_ids = []
    ntokens.append("[CLS]")
    segment_ids.append(0)
    # append("O") or append("[CLS]") not sure!
    label_ids.append(label_map["[CLS]"])
    for i, token in enumerate(tokens):
        ntokens.append(token)
        segment_ids.append(0)
        label_ids.append(label_map[labels[i]])
    ntokens.append("[SEP]")
    segment_ids.append(0)
    # append("O") or append("[SEP]") not sure!
    label_ids.append(label_map["[SEP]"])
    input_ids = tokenizer.convert_tokens_to_ids(ntokens)
    input_mask = [1] * len(input_ids)
    #label_mask = [1] * len(input_ids)
    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)
        # we don't concerned about it!
        label_ids.append(0)
        ntokens.append("**NULL**")
        #label_mask.append(0)
    # print(len(input_ids))
    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length
    assert len(label_ids) == max_seq_length
    #assert len(label_mask) == max_seq_length

    if ex_index < 5:
        tf.logging.info("*** Example ***")
        tf.logging.info("guid: %s" % (example.guid))
        tf.logging.info("tokens: %s" % " ".join(
            [tokenization.printable_text(x) for x in tokens]))
        tf.logging.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
        tf.logging.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
        tf.logging.info("segment_ids: %s" % " ".join([str(x) for x in segment_ids]))
        tf.logging.info("label_ids: %s" % " ".join([str(x) for x in label_ids]))
        #tf.logging.info("label_mask: %s" % " ".join([str(x) for x in label_mask]))

    feature = InputFeatures(
        input_ids=input_ids,
        input_mask=input_mask,
        segment_ids=segment_ids,
        label_ids=label_ids,
        #label_mask = label_mask
    )
    write_tokens(ntokens,mode)
    return feature


def filed_based_convert_examples_to_features(
        examples, label_list, max_seq_length, tokenizer, output_file,mode=None
):
    writer = tf.python_io.TFRecordWriter(output_file)
    for (ex_index, example) in enumerate(examples):
        if ex_index % 5000 == 0:
            tf.logging.info("Writing example %d of %d" % (ex_index, len(examples)))
        feature = convert_single_example(ex_index, example, label_list, max_seq_length, tokenizer,mode)
        
        def create_int_feature(values):
            f = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
            return f

        features = collections.OrderedDict()
        features["input_ids"] = create_int_feature(feature.input_ids)
        features["input_mask"] = create_int_feature(feature.input_mask)
        features["segment_ids"] = create_int_feature(feature.segment_ids)
        features["label_ids"] = create_int_feature(feature.label_ids)
        #features["label_mask"] = create_int_feature(feature.label_mask)
        tf_example = tf.train.Example(features=tf.train.Features(feature=features))
        writer.write(tf_example.SerializeToString())


def file_based_input_fn_builder(input_file, seq_length, is_training, drop_remainder):
    name_to_features = {
        "input_ids": tf.FixedLenFeature([seq_length], tf.int64),
        "input_mask": tf.FixedLenFeature([seq_length], tf.int64),
        "segment_ids": tf.FixedLenFeature([seq_length], tf.int64),
        "label_ids": tf.FixedLenFeature([seq_length], tf.int64),
        # "label_ids":tf.VarLenFeature(tf.int64),
        #"label_mask": tf.FixedLenFeature([seq_length], tf.int64),
    }

    def _decode_record(record, name_to_features):
        example = tf.parse_single_example(record, name_to_features)
        for name in list(example.keys()):
            t = example[name]
            if t.dtype == tf.int64:
                t = tf.to_int32(t)
            example[name] = t
        return example

    def input_fn(params):
        batch_size = params["batch_size"]
        d = tf.data.TFRecordDataset(input_file)
        if is_training:
            d = d.repeat()
            d = d.shuffle(buffer_size=100)
        d = d.apply(tf.contrib.data.map_and_batch(
            lambda record: _decode_record(record, name_to_features),
            batch_size=batch_size,
            drop_remainder=drop_remainder
        ))
        return d
    return input_fn


def create_model(bert_config, is_training, input_ids, input_mask,
                 segment_ids, labels, num_labels, use_one_hot_embeddings):
    model = modeling.BertModel(
        config=bert_config,
        is_training=is_training,
        input_ids=input_ids,
        input_mask=input_mask,
        token_type_ids=segment_ids,
        use_one_hot_embeddings=use_one_hot_embeddings
    )
    sequence_lengths = tf.reduce_sum(tf.sign(tf.abs(input_ids)),axis=1)
    #sequence_lengths = tf.subtract(sequence_lengths,len(sequence_lengths)*[2])
    output_layer = model.get_sequence_output()

    hidden_size = output_layer.shape[-1].value

    output_weight = tf.get_variable(
        "output_weights", [num_labels, hidden_size],
        initializer=tf.truncated_normal_initializer(stddev=0.02)
    )
    output_bias = tf.get_variable(
        "output_bias", [num_labels], initializer=tf.zeros_initializer()
    )
    with tf.variable_scope("loss"):
        if is_training:
            output_layer = tf.nn.dropout(output_layer, keep_prob=0.9)
        output_layer = tf.reshape(output_layer, [-1, hidden_size])
        logits = tf.matmul(output_layer, output_weight, transpose_b=True)
        logits = tf.nn.bias_add(logits, output_bias)
        logits = tf.reshape(logits, [-1, FLAGS.max_seq_length, num_labels])

        log_likelihood, transition_params = crf_log_likelihood(inputs=logits,tag_indices=labels,sequence_lengths=sequence_lengths)
        loss = -tf.reduce_mean(log_likelihood)
        predict,best_score = crf_decode(potentials=logits,transition_params=transition_params,sequence_length=sequence_lengths)

        # mask = tf.cast(input_mask,tf.float32)
        # loss = tf.contrib.seq2seq.sequence_loss(logits,labels,mask)
        # return (loss, logits, predict)
        ##########################################################################
        #log_probs = tf.nn.log_softmax(logits, axis=-1)
        #one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)
        #per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
        #loss = tf.reduce_sum(per_example_loss)
        #probabilities = tf.nn.softmax(logits, axis=-1)
        #predict = tf.argmax(probabilities,axis=-1)
        return (loss,logits,predict)
        ##########################################################################
        
def model_fn_builder(bert_config, num_labels, init_checkpoint, learning_rate,
                     num_train_steps, num_warmup_steps, use_tpu,
                     use_one_hot_embeddings):
    def model_fn(features, labels, mode, params):
        tf.logging.info("*** Features ***")
        for name in sorted(features.keys()):
            tf.logging.info("  name = %s, shape = %s" % (name, features[name].shape))
        input_ids = features["input_ids"]
        input_mask = features["input_mask"]
        segment_ids = features["segment_ids"]
        label_ids = features["label_ids"]
        #label_mask = features["label_mask"]
        is_training = (mode == tf.estimator.ModeKeys.TRAIN)

        (total_loss,logits,predicts) = create_model(
            bert_config, is_training, input_ids, input_mask,segment_ids, label_ids,
            num_labels, use_one_hot_embeddings)
        tvars = tf.trainable_variables()
        scaffold_fn = None
        if init_checkpoint:
            (assignment_map, initialized_variable_names) = modeling.get_assignment_map_from_checkpoint(tvars,init_checkpoint)
            tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
            if use_tpu:
                def tpu_scaffold():
                    tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
                    return tf.train.Scaffold()
                scaffold_fn = tpu_scaffold
            else:
                tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
        tf.logging.info("**** Trainable Variables ****")

        for var in tvars:
            init_string = ""
            if var.name in initialized_variable_names:
                init_string = ", *INIT_FROM_CKPT*"
            tf.logging.info("  name = %s, shape = %s%s", var.name, var.shape,
                            init_string)
        output_spec = None
        if mode == tf.estimator.ModeKeys.TRAIN:
            train_op = optimization.create_optimizer(
                total_loss, learning_rate, num_train_steps, num_warmup_steps, use_tpu)
            output_spec = tf.contrib.tpu.TPUEstimatorSpec(
                mode=mode,
                loss=total_loss,
                train_op=train_op,
                scaffold_fn=scaffold_fn)
        elif mode == tf.estimator.ModeKeys.EVAL:
            
            def metric_fn(label_ids, logits):
            # def metric_fn(label_ids, logits):

                #predictions = tf.argmax(logits, axis=-1, output_type=tf.int32)
                pos_indices = [i for i in range(2,num_labels-4)]
                precision = tf_metrics.precision(label_ids,predicts,num_labels,pos_indices,average="macro")
                recall = tf_metrics.recall(label_ids,predicts,num_labels,pos_indices,average="macro")
                f = tf_metrics.f1(label_ids,predicts,num_labels,pos_indices,average="macro")
                #
                return {
                    "eval_precision":precision,
                    "eval_recall":recall,
                    "eval_f": f,
                    #"eval_loss": loss,
                }
            eval_metrics = (metric_fn, [label_ids, logits])
            # eval_metrics = (metric_fn, [label_ids, logits])
            output_spec = tf.contrib.tpu.TPUEstimatorSpec(
                mode=mode,
                loss=total_loss,
                eval_metrics=eval_metrics,
                scaffold_fn=scaffold_fn)
        else:
            output_spec = tf.contrib.tpu.TPUEstimatorSpec(
                mode = mode,predictions= predicts,scaffold_fn=scaffold_fn
            )
        return output_spec
    return model_fn


def main(_):
    tf.logging.set_verbosity(tf.logging.INFO)
    processors = {
        "ner": NerProcessor
    }
    if not FLAGS.do_train and not FLAGS.do_eval and not FLAGS.do_predict:
        raise ValueError("At least one of `do_train` or `do_eval` or 'do_predict' must be True.")

    bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)

    if FLAGS.max_seq_length > bert_config.max_position_embeddings:
        raise ValueError(
            "Cannot use sequence length %d because the BERT model "
            "was only trained up to sequence length %d" %
            (FLAGS.max_seq_length, bert_config.max_position_embeddings))

    task_name = FLAGS.task_name.lower()
    if task_name not in processors:
        raise ValueError("Task not found: %s" % (task_name))
    processor = processors[task_name]()

    label_list = processor.get_labels()

    tokenizer = tokenization.FullTokenizer(
        vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)
    tpu_cluster_resolver = None
    if FLAGS.use_tpu and FLAGS.tpu_name:
        tpu_cluster_resolver = tf.contrib.cluster_resolver.TPUClusterResolver(
            FLAGS.tpu_name, zone=FLAGS.tpu_zone, project=FLAGS.gcp_project)

    is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2

    run_config = tf.contrib.tpu.RunConfig(
        cluster=tpu_cluster_resolver,
        master=FLAGS.master,
        model_dir=FLAGS.output_dir,
        save_checkpoints_steps=FLAGS.save_checkpoints_steps,
        tpu_config=tf.contrib.tpu.TPUConfig(
            iterations_per_loop=FLAGS.iterations_per_loop,
            num_shards=FLAGS.num_tpu_cores,
            per_host_input_for_training=is_per_host))

    train_examples = None
    num_train_steps = None
    num_warmup_steps = None

    if FLAGS.do_train:
        train_examples = processor.get_train_examples(FLAGS.data_dir)
        num_train_steps = int(
            len(train_examples) / FLAGS.train_batch_size * FLAGS.num_train_epochs)
        num_warmup_steps = int(num_train_steps * FLAGS.warmup_proportion)

    model_fn = model_fn_builder(
        bert_config=bert_config,
        num_labels=len(label_list)+1,
        init_checkpoint=FLAGS.init_checkpoint,
        learning_rate=FLAGS.learning_rate,
        num_train_steps=num_train_steps,
        num_warmup_steps=num_warmup_steps,
        use_tpu=FLAGS.use_tpu,
        use_one_hot_embeddings=FLAGS.use_tpu)

    estimator = tf.contrib.tpu.TPUEstimator(
        use_tpu=FLAGS.use_tpu,
        model_fn=model_fn,
        config=run_config,
        train_batch_size=FLAGS.train_batch_size,
        eval_batch_size=FLAGS.eval_batch_size,
        predict_batch_size=FLAGS.predict_batch_size)

    if FLAGS.do_train:
        train_file = os.path.join(FLAGS.output_dir, "train.tf_record")
        if not os.path.exists(train_file):
            filed_based_convert_examples_to_features(
                train_examples, label_list, FLAGS.max_seq_length, tokenizer, train_file)
        tf.logging.info("***** Running training *****")
        tf.logging.info("  Num examples = %d", len(train_examples))
        tf.logging.info("  Batch size = %d", FLAGS.train_batch_size)
        tf.logging.info("  Num steps = %d", num_train_steps)
        train_input_fn = file_based_input_fn_builder(
            input_file=train_file,
            seq_length=FLAGS.max_seq_length,
            is_training=True,
            drop_remainder=True)
        estimator.train(input_fn=train_input_fn, max_steps=num_train_steps)
    if FLAGS.do_eval:
        eval_examples = processor.get_dev_examples(FLAGS.data_dir)
        eval_file = os.path.join(FLAGS.output_dir, "eval.tf_record")
        filed_based_convert_examples_to_features(
            eval_examples, label_list, FLAGS.max_seq_length, tokenizer, eval_file)

        tf.logging.info("***** Running evaluation *****")
        tf.logging.info("  Num examples = %d", len(eval_examples))
        tf.logging.info("  Batch size = %d", FLAGS.eval_batch_size)
        eval_steps = None
        if FLAGS.use_tpu:
            eval_steps = int(len(eval_examples) / FLAGS.eval_batch_size)
        eval_drop_remainder = True if FLAGS.use_tpu else False
        eval_input_fn = file_based_input_fn_builder(
            input_file=eval_file,
            seq_length=FLAGS.max_seq_length,
            is_training=False,
            drop_remainder=eval_drop_remainder)
        result = estimator.evaluate(input_fn=eval_input_fn, steps=eval_steps)
        output_eval_file = os.path.join(FLAGS.output_dir, "eval_results.txt")
        with open(output_eval_file, "w") as writer:
            tf.logging.info("***** Eval results *****")
            for key in sorted(result.keys()):
                tf.logging.info("  %s = %s", key, str(result[key]))
                writer.write("%s = %s\n" % (key, str(result[key])))
    if FLAGS.do_predict:
        token_path = os.path.join(FLAGS.output_dir, "token_test.txt")
        with open(os.path.join(FLAGS.output_dir,'label2id.pkl'),'rb') as rf:
            label2id = pickle.load(rf)
            id2label = {value:key for key,value in label2id.items()}
            print('字典！！',id2label)
            print('大家分厘卡撒酒疯了')
            print(id2label[67])
        if os.path.exists(token_path):
            os.remove(token_path)
        predict_examples = processor.get_test_examples(FLAGS.data_dir)
        #print(predict_examples)
        predict_file = os.path.join(FLAGS.output_dir, "predict.tf_record")
        filed_based_convert_examples_to_features(predict_examples, label_list,
                                                FLAGS.max_seq_length, tokenizer,
                                                predict_file,mode="test")
                            
        tf.logging.info("***** Running prediction*****")
        tf.logging.info("  Num examples = %d", len(predict_examples))
        tf.logging.info("  Batch size = %d", FLAGS.predict_batch_size)
        if FLAGS.use_tpu:
            # Warning: According to tpu_estimator.py Prediction on TPU is an
            # experimental feature and hence not supported here
            raise ValueError("Prediction in TPU not supported")
        predict_drop_remainder = True if FLAGS.use_tpu else False
        predict_input_fn = file_based_input_fn_builder(
            input_file=predict_file,
            seq_length=FLAGS.max_seq_length,
            is_training=False,
            drop_remainder=predict_drop_remainder)

        result = estimator.predict(input_fn=predict_input_fn)
        output_predict_file = os.path.join(FLAGS.output_dir, "label_test.txt")
        with open(output_predict_file,'w') as writer:
            for prediction in result:
                output_line = "\n".join(id2label[id] for id in prediction if id!=0) + "\n"
                writer.write(output_line)

if __name__ == "__main__":
    flags.mark_flag_as_required("data_dir")
    flags.mark_flag_as_required("task_name")
    flags.mark_flag_as_required("vocab_file")
    flags.mark_flag_as_required("bert_config_file")
    flags.mark_flag_as_required("output_dir")
    tf.app.run()


