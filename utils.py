import logging, sys, argparse

# all_class = ['为劫取财物预谋杀人','以非法占有为目的','以非法占有为目的，采用暴力、胁迫手段迫使他人交出与合理价钱、费用相差悬殊的钱物','入户抢劫',
# '公私财物','冒充人民警察或治安联防队员，以暴力或暴力相威胁没收赌资或罚款','冒充军警人员抢劫','在交通工具上抢劫','多次抢劫','多次结伙抢劫',
# '已满十四周岁不满十六周岁对抢劫罪负责','抢劫中为制服被害人杀人','抢劫数额巨大','抢劫罪-共犯','抢劫罪-未遂','抢劫致人重伤、死亡','抢劫银行或其他金融机构',
# '持枪抢劫','携带凶器抢夺','暴力、胁迫或者以其他方式抢劫','转化抢劫','转化抢劫数额未达到“数额较大”，情节较轻，危害不大','违禁品、违法所得、犯罪所得及其收益','驾驶机动车抢劫']

# all_class = ['O', '盗窃文物', '偷拿家庭成员或者近亲属的财物，追究刑事责任的',
#              '采用破坏性手段盗窃古文化遗址、古墓葬以外的（古建筑、石窟寺、石刻、壁画、近代现代重要史迹和代表性建筑等）其他不可移动文物',
#              '盗窃罪-共犯', '将国家、集体、他人所有并已经伐倒的树木窃为己有', '数额较大', '多次盗窃', '数额巨大', '邮政工作人员窃取邮件财物',
#              '公私财物', '采用破坏性手段盗窃公私财物，造成其他财物损毁', '以非法占有为目的', '盗窃数额提取', '未成年人盗窃未遂或中止', '数额特别巨大',
#              '未成年人盗窃数额较大，未超过三次，如实供述积极退赃，具有其他轻微情节', '入户盗窃', '偷拿家庭成员或近亲属财物，获得谅解',
#              '盗窃油气或者正在使用的油气设备，构成犯罪，但未危害公共安全', '金额_盗窃金额', '未成年人盗窃自己家庭或者近亲属财物', '偷砍他人房前屋后、自留地种植的零星树木',
#              '一般盗窃行为', '秘密窃取', '以牟利为目的，盗接他人通信线路、复制他人电信码号', '携带凶器盗窃', '盗窃数额较大，行为人认罪悔罪，退赃退赔，被害人谅解，情节轻微',
#              '采用破坏性手段盗窃古文化遗址、古墓葬以外的（古建筑、石窟寺、石刻、壁画、近代现>代重要史迹和代表性建筑等）其他不可移动文物',
#              '未成年人起次要或辅助作用，或被胁迫盗窃数额较大，未超过三次，如实供述积极退赃', '其他严重情节', '盗窃信用卡并使用', '扒窃']



def str2bool(v):
    # copy from StackOverflow
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def get_entity(tag_seq, char_seq,all_class):
    # PER = get_PER_entity(tag_seq, char_seq)
    # LOC = get_LOC_entity(tag_seq, char_seq)
    # ORG = get_ORG_entity(tag_seq, char_seq)
    # return PER, LOC, ORG
    return get_all_entity(all_class,tag_seq,char_seq)


def get_PER_entity(tag_seq, char_seq):
    length = len(char_seq)
    PER = []
    for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
        if tag == 'B-PER':
            if 'per' in locals().keys():
                PER.append(per)
                del per
            per = char
            if i+1 == length:
                PER.append(per)
        if tag == 'I-PER':
            per += char
            if i+1 == length:
                PER.append(per)
        if tag not in ['I-PER', 'B-PER']:
            if 'per' in locals().keys():
                PER.append(per)
                del per
            continue
    return PER


def get_LOC_entity(tag_seq, char_seq):
    length = len(char_seq)
    LOC = []
    for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
        if tag == 'B-LOC':
            if 'loc' in locals().keys():
                LOC.append(loc)
                del loc
            loc = char
            if i+1 == length:
                LOC.append(loc)
        if tag == 'I-LOC':
            loc += char
            if i+1 == length:
                LOC.append(loc)
        if tag not in ['I-LOC', 'B-LOC']:
            if 'loc' in locals().keys():
                LOC.append(loc)
                del loc
            continue
    return LOC


def get_ORG_entity(tag_seq, char_seq):
    length = len(char_seq)
    ORG = []
    for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
        if tag == 'B-ORG':
            if 'org' in locals().keys():
                ORG.append(org)
                del org
            org = char
            if i+1 == length:
                ORG.append(org)
        if tag == 'I-ORG':
            org += char
            if i+1 == length:
                ORG.append(org)
        if tag not in ['I-ORG', 'B-ORG']:
            if 'org' in locals().keys():
                ORG.append(org)
                del org
            continue
    return ORG


def get_all_entity(all_class,tag_seq, char_seq):
    length = len(char_seq)
    result = {}
    for any_class in all_class:
        ENTITY = []
        for i, (char, tag) in enumerate(zip(char_seq, tag_seq)):
            # print(locals().keys())
            if tag == 'B-'+any_class:
                if 'entity' in locals().keys():
                    ENTITY.append(entity)
                    del entity
                entity = char
                if i+1 == length:
                    ENTITY.append(entity)
            if tag == 'I-'+any_class:
                try:
                    entity += char
                except Exception as e:
                    entity = char
                if i+1 == length:
                    ENTITY.append(entity)
            if tag not in ['B-'+any_class,'I-'+any_class]:
                if 'entity' in locals().keys():
                    ENTITY.append(entity)
                    del entity
                continue
        result[any_class] = ENTITY
    return result







def get_logger(filename):
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    handler = logging.FileHandler(filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s: %(message)s'))
    logging.getLogger().addHandler(handler)
    return logger


