"""种子数据脚本：30首诗词 + 20条节日 + 课本数据

用法：
    python -m app.data.seed
"""

import asyncio
import json
import uuid
from datetime import date, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, engine, Base
from app.models.poem import Poem
from app.models.event import Festival
from app.models.recommendation import DailyRecommendation
from app.models.textbook import Textbook, PoemTextbook


def uid(name: str) -> str:
    """生成稳定的 UUID（基于名称）"""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ttbs-seed-{name}"))


# ============================================================
# 诗词种子数据（30首）
# ============================================================

POEMS = [
    {
        "id": uid("poem-001"),
        "title": "静夜思",
        "author": "李白",
        "dynasty": "唐",
        "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
        "content_lines": json.dumps(["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"], ensure_ascii=False),
        "annotation": json.dumps(["静夜思：在寂静的夜晚思念故乡。", "疑：好像。", "举头：抬头。"], ensure_ascii=False),
        "translation": "明亮的月光洒在窗户纸上，好像地上泛起了一层白霜。我抬起头来，看那天窗外空中的一轮明月，不由得低头沉思，想起远方的家乡。",
        "background": "李白26岁时在扬州旅舍所作，表达游子思乡之情。",
        "difficulty": 1,
        "tags": "意象:月|主题:思乡|场景:秋夜",
        "scene_type": "月夜",
        "scene_desc": "秋夜静谧，明月高悬，游子独坐窗前，银辉洒地如霜。",
    },
    {
        "id": uid("poem-002"),
        "title": "春晓",
        "author": "孟浩然",
        "dynasty": "唐",
        "content": "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
        "content_lines": json.dumps(["春眠不觉晓，", "处处闻啼鸟。", "夜来风雨声，", "花落知多少。"], ensure_ascii=False),
        "annotation": json.dumps(["春晓：春天的早晨。", "不觉晓：不知不觉天就亮了。", "闻啼鸟：听到鸟儿的叫声。"], ensure_ascii=False),
        "translation": "春日里贪睡，不知不觉天已破晓，醒来只听到处处有鸟儿啼叫。想起昨夜里的阵阵风雨声，不知花儿被吹落了多少。",
        "background": "诗人隐居鹿门山时所作，意境优美，表达了诗人对春天的热爱和惜春之情。",
        "difficulty": 1,
        "tags": "意象:鸟,意象:花,意象:风雨|主题:惜春|场景:清晨",
        "scene_type": "春晨",
        "scene_desc": "春日清晨，阳光初照，窗外鸟儿啼鸣，地上落花点点。",
    },
    {
        "id": uid("poem-003"),
        "title": "登鹳雀楼",
        "author": "王之涣",
        "dynasty": "唐",
        "content": "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。",
        "content_lines": json.dumps(["白日依山尽，", "黄河入海流。", "欲穷千里目，", "更上一层楼。"], ensure_ascii=False),
        "annotation": json.dumps(["鹳雀楼：旧址在山西永济。", "依：依傍。", "穷：尽，使达到极点。"], ensure_ascii=False),
        "translation": "夕阳依傍着西山慢慢地沉没，滔滔黄河朝着东海汹涌奔流。若想把千里的风光景物看够，那就要登上更高的一层城楼。",
        "background": "诗人登鹳雀楼望远有感而作，以景入理，寓意深远。",
        "difficulty": 1,
        "tags": "意象:白日,意象:黄河,意象:山|主题:登高,主题:哲理|场景:黄昏",
        "scene_type": "登高望远",
        "scene_desc": "夕阳西下，黄河东流，诗人登楼远眺，天地辽阔尽收眼底。",
    },
    {
        "id": uid("poem-004"),
        "title": "咏鹅",
        "author": "骆宾王",
        "dynasty": "唐",
        "content": "鹅，鹅，鹅，曲项向天歌。白毛浮绿水，红掌拨清波。",
        "content_lines": json.dumps(["鹅，鹅，鹅，", "曲项向天歌。", "白毛浮绿水，", "红掌拨清波。"], ensure_ascii=False),
        "annotation": json.dumps(["曲项：弯着脖子。", "歌：鸣叫。", "拨：划动。"], ensure_ascii=False),
        "translation": "鹅，鹅，鹅！弯曲着脖子朝天欢叫。洁白的羽毛漂浮在碧绿的水面上，红红的脚掌拨动着清清的水波。",
        "background": "骆宾王七岁时所作，是中国儿童启蒙诗歌的经典之作。",
        "difficulty": 1,
        "tags": "意象:鹅,意象:绿水|主题:咏物,主题:童趣|场景:水边",
        "scene_type": "池塘",
        "scene_desc": "碧绿的池水中，白鹅悠然游动，红掌拨水泛起涟漪。",
    },
    {
        "id": uid("poem-005"),
        "title": "悯农（其二）",
        "author": "李绅",
        "dynasty": "唐",
        "content": "锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。",
        "content_lines": json.dumps(["锄禾日当午，", "汗滴禾下土。", "谁知盘中餐，", "粒粒皆辛苦。"], ensure_ascii=False),
        "annotation": json.dumps(["锄禾：用锄头松土除草。", "日当午：中午太阳正烈。", "餐：饭食。"], ensure_ascii=False),
        "translation": "农民在正午烈日下锄禾，汗水滴在禾苗下的泥土中。有谁知道盘中的饭食，每一粒都饱含着农民的辛苦。",
        "background": "诗人看到农民辛勤劳作而作，表达了珍惜粮食、同情劳动人民的感情。",
        "difficulty": 1,
        "tags": "意象:烈日,意象:汗滴,意象:禾|主题:悯农,主题:珍惜|场景:农田",
        "scene_type": "农田",
        "scene_desc": "正午烈日当空，农夫挥汗如雨在田间劳作。",
    },
    {
        "id": uid("poem-006"),
        "title": "望庐山瀑布",
        "author": "李白",
        "dynasty": "唐",
        "content": "日照香炉生紫烟，遥看瀑布挂前川。飞流直下三千尺，疑是银河落九天。",
        "content_lines": json.dumps(["日照香炉生紫烟，", "遥看瀑布挂前川。", "飞流直下三千尺，", "疑是银河落九天。"], ensure_ascii=False),
        "annotation": json.dumps(["香炉：香炉峰。", "紫烟：日光照射水气形成的紫色烟雾。", "九天：天空最高处。"], ensure_ascii=False),
        "translation": "太阳照射香炉峰升起紫色烟雾，远远望去瀑布像白色绸带挂在山前。水流飞泻而下三千尺，让人怀疑是银河从九天之上落下来。",
        "background": "李白游庐山时所作，以夸张手法描绘庐山瀑布的壮丽景象。",
        "difficulty": 2,
        "tags": "意象:瀑布,意象:银河,意象:紫烟|主题:山水,主题:壮丽|场景:庐山",
        "scene_type": "山水",
        "scene_desc": "庐山香炉峰云雾缭绕，瀑布如白练飞泻而下，气势磅礴。",
    },
    {
        "id": uid("poem-007"),
        "title": "江雪",
        "author": "柳宗元",
        "dynasty": "唐",
        "content": "千山鸟飞绝，万径人踪灭。孤舟蓑笠翁，独钓寒江雪。",
        "content_lines": json.dumps(["千山鸟飞绝，", "万径人踪灭。", "孤舟蓑笠翁，", "独钓寒江雪。"], ensure_ascii=False),
        "annotation": json.dumps(["绝：消失。", "万径：指千万条路。", "蓑笠：蓑衣和斗笠。"], ensure_ascii=False),
        "translation": "所有的山上都看不到飞鸟的影子，所有的路上都没有人的踪迹。只有江面上一只小船上，一个披着蓑衣戴着斗笠的老人，独自在漫天风雪中垂钓。",
        "background": "柳宗元被贬永州时所作，借寒江独钓表达不屈的精神和孤傲的性格。",
        "difficulty": 2,
        "tags": "意象:雪,意象:孤舟,意象:寒江|主题:孤独,主题:坚韧|场景:雪景",
        "scene_type": "雪景",
        "scene_desc": "漫天飞雪中，千山万径空无一人，唯有一叶孤舟、一位老翁在寒江上垂钓。",
    },
    {
        "id": uid("poem-008"),
        "title": "游子吟",
        "author": "孟郊",
        "dynasty": "唐",
        "content": "慈母手中线，游子身上衣。临行密密缝，意恐迟迟归。谁言寸草心，报得三春晖。",
        "content_lines": json.dumps(["慈母手中线，游子身上衣。", "临行密密缝，意恐迟迟归。", "谁言寸草心，报得三春晖。"], ensure_ascii=False),
        "annotation": json.dumps(["游子：离家远行的人。", "意恐：担心。", "寸草心：小草的心意，比喻子女的孝心。", "三春晖：春天的阳光，比喻母爱。"], ensure_ascii=False),
        "translation": "慈祥的母亲手里拿着针线，为即将远行的孩子赶制新衣。临行前一针针密密地缝缀，怕孩子在外迟迟不能归来。谁说像小草那样微弱的孝心，能报答得了像春晖普泽的慈母恩情？",
        "background": "孟郊五十岁任溧阳县尉时，接母亲同住，有感而作。",
        "difficulty": 2,
        "tags": "意象:慈母,意象:针线,意象:春晖|主题:母爱,主题:感恩|场景:离别",
        "scene_type": "离别",
        "scene_desc": "昏黄的灯光下，母亲一针一线为即将远行的儿子缝制衣裳。",
    },
    {
        "id": uid("poem-009"),
        "title": "元日",
        "author": "王安石",
        "dynasty": "宋",
        "content": "爆竹声中一岁除，春风送暖入屠苏。千门万户曈曈日，总把新桃换旧符。",
        "content_lines": json.dumps(["爆竹声中一岁除，", "春风送暖入屠苏。", "千门万户曈曈日，", "总把新桃换旧符。"], ensure_ascii=False),
        "annotation": json.dumps(["元日：农历正月初一。", "屠苏：屠苏酒。", "曈曈：日出时光亮的样子。", "新桃换旧符：用新桃符换下旧桃符。"], ensure_ascii=False),
        "translation": "在阵阵鞭炮声中送走旧岁迎来新年，人们迎着和煦的春风开怀畅饮屠苏酒。初升的太阳照耀着千家万户，大家都忙着把旧的桃符取下换上新的桃符。",
        "background": "王安石变法初期所作，借新年新气象表达改革的决心与希望。",
        "difficulty": 2,
        "tags": "意象:爆竹,意象:春风,意象:桃符|主题:春节,主题:迎新|场景:春节",
        "scene_type": "春节",
        "scene_desc": "大年初一，爆竹声声辞旧迎新，家家户户贴上新桃符，充满喜悦。",
    },
    {
        "id": uid("poem-010"),
        "title": "清明",
        "author": "杜牧",
        "dynasty": "唐",
        "content": "清明时节雨纷纷，路上行人欲断魂。借问酒家何处有，牧童遥指杏花村。",
        "content_lines": json.dumps(["清明时节雨纷纷，", "路上行人欲断魂。", "借问酒家何处有，", "牧童遥指杏花村。"], ensure_ascii=False),
        "annotation": json.dumps(["清明：二十四节气之一。", "欲断魂：形容十分伤感。", "借问：请问。"], ensure_ascii=False),
        "translation": "清明时节细雨纷纷飘洒，路上羁旅行人个个落魄断魂。询问当地之人何处可以买酒浇愁，牧童笑而不答遥指远处的杏花山村。",
        "background": "诗人清明时节行路遇雨有感而作。",
        "difficulty": 2,
        "tags": "意象:春雨,意象:杏花,意象:牧童|主题:清明,主题:乡愁|场景:清明",
        "scene_type": "清明",
        "scene_desc": "清明时节，细雨蒙蒙，路上行人神色黯然，远处杏花深处酒旗招展。",
    },
    {
        "id": uid("poem-011"),
        "title": "凉州词",
        "author": "王翰",
        "dynasty": "唐",
        "content": "葡萄美酒夜光杯，欲饮琵琶马上催。醉卧沙场君莫笑，古来征战几人回。",
        "content_lines": json.dumps(["葡萄美酒夜光杯，", "欲饮琵琶马上催。", "醉卧沙场君莫笑，", "古来征战几人回。"], ensure_ascii=False),
        "annotation": json.dumps(["夜光杯：用美玉制成的酒杯。", "催：催促出发。", "沙场：战场。"], ensure_ascii=False),
        "translation": "酒筵上甘醇的葡萄美酒盛满在夜光杯中，正要畅饮时马上琵琶也声声响起仿佛催人出征。如果醉倒在战场上请你不要笑话，从古至今外出征战的有几人能平安归来？",
        "background": "描写边塞将士豪迈悲壮的军旅生活。",
        "difficulty": 2,
        "tags": "意象:美酒,意象:琵琶,意象:沙场|主题:边塞,主题:豪迈|场景:边塞",
        "scene_type": "边塞",
        "scene_desc": "边塞军营中，将士们举杯畅饮，琵琶声起催人出征，豪情与悲壮交织。",
    },
    {
        "id": uid("poem-012"),
        "title": "出塞",
        "author": "王昌龄",
        "dynasty": "唐",
        "content": "秦时明月汉时关，万里长征人未还。但使龙城飞将在，不教胡马度阴山。",
        "content_lines": json.dumps(["秦时明月汉时关，", "万里长征人未还。", "但使龙城飞将在，", "不教胡马度阴山。"], ensure_ascii=False),
        "annotation": json.dumps(["龙城飞将：指汉代名将李广。", "胡马：指敌人的骑兵。", "阴山：北方山脉。"], ensure_ascii=False),
        "translation": "依旧是秦时的明月汉时的边关，万里出征的将士仍未归还。只要有李广那样的名将镇守边关，就一定不会让敌人的铁骑踏过阴山。",
        "background": "慨叹边战不断、国无良将的边塞诗。",
        "difficulty": 2,
        "tags": "意象:明月,意象:边关|主题:边塞,主题:爱国|场景:边关",
        "scene_type": "边关",
        "scene_desc": "边关月夜，将士遥望远方，思念故乡又誓死守卫边疆。",
    },
    {
        "id": uid("poem-013"),
        "title": "枫桥夜泊",
        "author": "张继",
        "dynasty": "唐",
        "content": "月落乌啼霜满天，江枫渔火对愁眠。姑苏城外寒山寺，夜半钟声到客船。",
        "content_lines": json.dumps(["月落乌啼霜满天，", "江枫渔火对愁眠。", "姑苏城外寒山寺，", "夜半钟声到客船。"], ensure_ascii=False),
        "annotation": json.dumps(["姑苏：苏州的别称。", "寒山寺：苏州城西的寺院。", "夜半钟声：当时寺院有半夜敲钟的习惯。"], ensure_ascii=False),
        "translation": "月亮已落下，乌鸦啼叫，寒气满天。对着江边枫树和渔火忧愁而眠。姑苏城外那寂寞清静的寒山古寺，半夜里敲钟的声音传到了客船上。",
        "background": "诗人途经寒山寺，夜泊枫桥的夜景抒写羁旅之思。",
        "difficulty": 2,
        "tags": "意象:月落,意象:乌啼,意象:钟声,意象:渔火|主题:羁旅,主题:愁思|场景:秋夜",
        "scene_type": "秋夜",
        "scene_desc": "深秋夜晚，客船停泊枫桥边，远处寒山寺钟声悠扬，江枫渔火映着愁眠。",
    },
    {
        "id": uid("poem-014"),
        "title": "望岳",
        "author": "杜甫",
        "dynasty": "唐",
        "content": "岱宗夫如何，齐鲁青未了。造化钟神秀，阴阳割昏晓。荡胸生曾云，决眦入归鸟。会当凌绝顶，一览众山小。",
        "content_lines": json.dumps(["岱宗夫如何，齐鲁青未了。", "造化钟神秀，阴阳割昏晓。", "荡胸生曾云，决眦入归鸟。", "会当凌绝顶，一览众山小。"], ensure_ascii=False),
        "annotation": json.dumps(["岱宗：泰山。", "造化：大自然。", "钟：聚集。", "决眦：眼角几乎要裂开。"], ensure_ascii=False),
        "translation": "泰山到底怎么样？在齐鲁大地上那青翠的山色没有尽头。大自然把神奇秀丽的景色都汇聚在泰山，山南山北分隔出清晨和黄昏。层层白云荡涤胸中丘壑，翩翩归鸟飞入赏景眼圈。定要登上泰山最高峰，俯瞰群山豪情满怀。",
        "background": "杜甫青年时期游泰山所作，表达了诗人不怕困难、敢于攀登的雄心。",
        "difficulty": 3,
        "tags": "意象:泰山,意象:云海,意象:归鸟|主题:登高,主题:壮志|场景:泰山",
        "scene_type": "山岳",
        "scene_desc": "巍峨泰山，云海翻腾，诗人极目远眺，心生登顶凌绝之志。",
    },
    {
        "id": uid("poem-015"),
        "title": "黄鹤楼送孟浩然之广陵",
        "author": "李白",
        "dynasty": "唐",
        "content": "故人西辞黄鹤楼，烟花三月下扬州。孤帆远影碧空尽，唯见长江天际流。",
        "content_lines": json.dumps(["故人西辞黄鹤楼，", "烟花三月下扬州。", "孤帆远影碧空尽，", "唯见长江天际流。"], ensure_ascii=False),
        "annotation": json.dumps(["之：去，到。", "烟花：形容柳絮如烟、繁花似锦的春天。", "碧空尽：在碧蓝的天空中消失。"], ensure_ascii=False),
        "translation": "老朋友在黄鹤楼与我辞别，在柳絮如烟、繁花似锦的阳春三月去扬州远游。友人的孤船帆影渐渐地远去消失在碧空的尽头，只看见一线长江向天边奔流。",
        "background": "李白在黄鹤楼送别孟浩然时所作，以景寓情。",
        "difficulty": 3,
        "tags": "意象:黄鹤楼,意象:孤帆,意象:长江|主题:送别,主题:友情|场景:送别",
        "scene_type": "送别",
        "scene_desc": "黄鹤楼上，烟花三月，友人乘船远去，孤帆消失在天际，唯有长江水滚滚东流。",
    },
    {
        "id": uid("poem-016"),
        "title": "绝句",
        "author": "杜甫",
        "dynasty": "唐",
        "content": "两个黄鹂鸣翠柳，一行白鹭上青天。窗含西岭千秋雪，门泊东吴万里船。",
        "content_lines": json.dumps(["两个黄鹂鸣翠柳，", "一行白鹭上青天。", "窗含西岭千秋雪，", "门泊东吴万里船。"], ensure_ascii=False),
        "annotation": json.dumps(["黄鹂：黄莺。", "白鹭：一种水鸟。", "西岭：成都西边的岷山。"], ensure_ascii=False),
        "translation": "两只黄鹂在翠绿的柳树间婉转歌唱，一队整齐的白鹭直冲向蔚蓝的天空。我坐在窗前可以望见西岭上堆积着终年不化的积雪，门前停泊着自万里外的东吴远行而来的船只。",
        "background": "杜甫流寓成都时所作，描绘了草堂周围的生机盎然。",
        "difficulty": 2,
        "tags": "意象:黄鹂,意象:翠柳,意象:白鹭,意象:雪山|主题:春景,主题:生机|场景:春日",
        "scene_type": "春日",
        "scene_desc": "春光明媚，翠柳依依，黄鹂鸣翠柳，白鹭上青天，窗前雪山静静伫立。",
    },
    {
        "id": uid("poem-017"),
        "title": "九月九日忆山东兄弟",
        "author": "王维",
        "dynasty": "唐",
        "content": "独在异乡为异客，每逢佳节倍思亲。遥知兄弟登高处，遍插茱萸少一人。",
        "content_lines": json.dumps(["独在异乡为异客，", "每逢佳节倍思亲。", "遥知兄弟登高处，", "遍插茱萸少一人。"], ensure_ascii=False),
        "annotation": json.dumps(["九月九日：重阳节。", "茱萸：一种植物，古人重阳节佩戴以辟邪。"], ensure_ascii=False),
        "translation": "独自漂泊在外作异乡之客，每逢佳节到来就更加思念亲人。遥想家乡的兄弟们今天都在登高，头上都插着茱萸，只少了我一个人。",
        "background": "王维十七岁时为思念家乡兄弟所作。",
        "difficulty": 2,
        "tags": "意象:异乡,意象:茱萸|主题:思乡,主题:重阳|场景:重阳",
        "scene_type": "重阳",
        "scene_desc": "重阳佳节，诗人独在异乡，遥想家乡兄弟登高插茱萸的场景。",
    },
    {
        "id": uid("poem-018"),
        "title": "饮湖上初晴后雨",
        "author": "苏轼",
        "dynasty": "宋",
        "content": "水光潋滟晴方好，山色空蒙雨亦奇。欲把西湖比西子，淡妆浓抹总相宜。",
        "content_lines": json.dumps(["水光潋滟晴方好，", "山色空蒙雨亦奇。", "欲把西湖比西子，", "淡妆浓抹总相宜。"], ensure_ascii=False),
        "annotation": json.dumps(["潋滟：水波荡漾的样子。", "空蒙：细雨迷茫的样子。", "西子：西施。"], ensure_ascii=False),
        "translation": "晴天西湖水面波光粼粼十分美丽，雨天山色在雨幕中朦胧也很奇妙。想把西湖比作美女西施，无论是淡妆还是浓抹都是那么美丽适宜。",
        "background": "苏轼任杭州通判时游西湖所作。",
        "difficulty": 2,
        "tags": "意象:西湖,意象:水光,意象:山色|主题:山水,主题:咏景|场景:西湖",
        "scene_type": "西湖",
        "scene_desc": "西湖晴雨皆美，晴时波光潋滟，雨时山色空蒙，如西子淡妆浓抹。",
    },
    {
        "id": uid("poem-019"),
        "title": "题西林壁",
        "author": "苏轼",
        "dynasty": "宋",
        "content": "横看成岭侧成峰，远近高低各不同。不识庐山真面目，只缘身在此山中。",
        "content_lines": json.dumps(["横看成岭侧成峰，", "远近高低各不同。", "不识庐山真面目，", "只缘身在此山中。"], ensure_ascii=False),
        "annotation": json.dumps(["西林：庐山西林寺。", "缘：因为。"], ensure_ascii=False),
        "translation": "从正面看庐山是连绵的山岭，从侧面看则是陡峭的山峰。从远、近、高、低不同角度看，庐山呈现不同的样子。我之所以认不清庐山的真面目，是因为我自己就身在这庐山之中。",
        "background": "苏轼游庐山时在西林寺墙壁上题写，寓含深刻哲理。",
        "difficulty": 2,
        "tags": "意象:庐山,意象:山峰|主题:山水,主题:哲理|场景:庐山",
        "scene_type": "山岳",
        "scene_desc": "庐山千姿百态，横看是岭侧看成峰，远近高低各不相同。",
    },
    {
        "id": uid("poem-020"),
        "title": "泊船瓜洲",
        "author": "王安石",
        "dynasty": "宋",
        "content": "京口瓜洲一水间，钟山只隔数重山。春风又绿江南岸，明月何时照我还。",
        "content_lines": json.dumps(["京口瓜洲一水间，", "钟山只隔数重山。", "春风又绿江南岸，", "明月何时照我还。"], ensure_ascii=False),
        "annotation": json.dumps(["瓜洲：在长江北岸。", "京口：今江苏镇江。", "钟山：南京紫金山。"], ensure_ascii=False),
        "translation": "京口和瓜洲之间只隔着一条长江，钟山也只隔着几重山峦。春风又把江南岸吹绿了，明月什么时候才能照着我回到家乡呢？",
        "background": "王安石第二次拜相，奉诏进京途经瓜洲时所作。",
        "difficulty": 2,
        "tags": "意象:春风,意象:江南,意象:明月|主题:思乡,主题:春景|场景:江南",
        "scene_type": "江南",
        "scene_desc": "江南岸春风拂绿，明月当空，诗人泊船瓜洲，遥望钟山思念故乡。",
    },
    {
        "id": uid("poem-021"),
        "title": "赠汪伦",
        "author": "李白",
        "dynasty": "唐",
        "content": "李白乘舟将欲行，忽闻岸上踏歌声。桃花潭水深千尺，不及汪伦送我情。",
        "content_lines": json.dumps(["李白乘舟将欲行，", "忽闻岸上踏歌声。", "桃花潭水深千尺，", "不及汪伦送我情。"], ensure_ascii=False),
        "annotation": json.dumps(["踏歌：边唱歌边用脚踏地作节拍。", "桃花潭：在今安徽泾县。", "汪伦：李白的朋友。"], ensure_ascii=False),
        "translation": "李白坐上小船刚要出发，忽然听到岸上传来踏歌之声。桃花潭水即使深有千尺，也比不上汪伦送我的情谊深厚。",
        "background": "李白游历安徽时与当地村民汪伦结下深厚友谊，离别时汪伦踏歌相送。",
        "difficulty": 1,
        "tags": "意象:桃花潭,意象:舟|主题:送别,主题:友情|场景:送别",
        "scene_type": "送别",
        "scene_desc": "桃花潭边，李白登舟将行，岸上汪伦踏歌相送，情深意重。",
    },
    {
        "id": uid("poem-022"),
        "title": "早发白帝城",
        "author": "李白",
        "dynasty": "唐",
        "content": "朝辞白帝彩云间，千里江陵一日还。两岸猿声啼不住，轻舟已过万重山。",
        "content_lines": json.dumps(["朝辞白帝彩云间，", "千里江陵一日还。", "两岸猿声啼不住，", "轻舟已过万重山。"], ensure_ascii=False),
        "annotation": json.dumps(["白帝城：在今重庆奉节。", "江陵：今湖北荆州。", "万重山：层层叠叠的山。"], ensure_ascii=False),
        "translation": "清晨告别彩云缭绕的白帝城，千里之遥的江陵一天就能到达。两岸猿猴的啼声还在耳边不停回荡，轻快的小船已经驶过连绵不绝的万重山峦。",
        "background": "李白流放夜郎途中遇赦，返回时所作，表达了重获自由的欢快心情。",
        "difficulty": 2,
        "tags": "意象:白帝城,意象:轻舟,意象:万重山|主题:山水,主题:归途|场景:三峡",
        "scene_type": "三峡",
        "scene_desc": "清晨三峡云雾缭绕，一叶轻舟顺流而下，两岸猿声不绝，穿行于万重山间。",
    },
    {
        "id": uid("poem-023"),
        "title": "赋得古原草送别",
        "author": "白居易",
        "dynasty": "唐",
        "content": "离离原上草，一岁一枯荣。野火烧不尽，春风吹又生。远芳侵古道，晴翠接荒城。又送王孙去，萋萋满别情。",
        "content_lines": json.dumps(["离离原上草，一岁一枯荣。", "野火烧不尽，春风吹又生。", "远芳侵古道，晴翠接荒城。", "又送王孙去，萋萋满别情。"], ensure_ascii=False),
        "annotation": json.dumps(["离离：青草茂盛的样子。", "王孙：贵族子孙，此处指远行的友人。", "萋萋：草长得茂盛的样子。"], ensure_ascii=False),
        "translation": "古原上的野草繁密茂盛，每年春天繁盛秋天枯萎。野火无法把它烧尽，春风一吹它又生长起来。远处的芳草蔓延到古老的道路上，阳光下的翠绿连接着荒凉的城墙。又送别朋友远去，这满原的萋萋芳草充满了离别之情。",
        "background": "白居易十六岁时应考习作，以春草比喻离别之情。",
        "difficulty": 3,
        "tags": "意象:春草,意象:古道,意象:荒城|主题:送别,主题:生命力|场景:送别",
        "scene_type": "送别",
        "scene_desc": "古原之上春草萋萋，远芳侵古道，诗人在此送别友人。",
    },
    {
        "id": uid("poem-024"),
        "title": "春夜喜雨",
        "author": "杜甫",
        "dynasty": "唐",
        "content": "好雨知时节，当春乃发生。随风潜入夜，润物细无声。野径云俱黑，江船火独明。晓看红湿处，花重锦官城。",
        "content_lines": json.dumps(["好雨知时节，当春乃发生。", "随风潜入夜，润物细无声。", "野径云俱黑，江船火独明。", "晓看红湿处，花重锦官城。"], ensure_ascii=False),
        "annotation": json.dumps(["知：明白。", "乃：就。", "潜：悄悄地。", "锦官城：成都的别称。"], ensure_ascii=False),
        "translation": "好雨似乎会挑选时节，在春天来到的时候就伴着春风在夜晚悄悄地下起来。它无声地滋润着万物，野外小路上空乌云一片漆黑，只有江船上的灯火独自明亮。天亮后看那被雨水润湿的花丛，锦官城的花显得格外饱满沉重。",
        "background": "杜甫在成都草堂居住时所作，描写春雨润物的喜悦。",
        "difficulty": 3,
        "tags": "意象:春雨,意象:江船,意象:花|主题:咏雨,主题:喜春|场景:雨夜",
        "scene_type": "雨夜",
        "scene_desc": "春夜细雨随风潜入，润物无声，江船灯火点点，天明后花开满城。",
    },
    {
        "id": uid("poem-025"),
        "title": "忆江南",
        "author": "白居易",
        "dynasty": "唐",
        "content": "江南好，风景旧曾谙。日出江花红胜火，春来江水绿如蓝。能不忆江南？",
        "content_lines": json.dumps(["江南好，风景旧曾谙。", "日出江花红胜火，春来江水绿如蓝。", "能不忆江南？"], ensure_ascii=False),
        "annotation": json.dumps(["谙：熟悉。", "江花：江边的花朵。", "蓝：蓝草，可制靛青染料。"], ensure_ascii=False),
        "translation": "江南的风景多么美好，如画的风景我早已熟悉。春天到来时太阳从江面升起，把江边的鲜花照得比火还红，碧绿的江水绿得胜过蓝草。怎能不让人怀念江南？",
        "background": "白居易曾任杭州、苏州刺史，对江南有深厚感情。",
        "difficulty": 2,
        "tags": "意象:日出,意象:江花,意象:江水|主题:江南,主题:忆旧|场景:江南",
        "scene_type": "江南",
        "scene_desc": "江南春日，日出江花红胜火，江水绿如蓝，美不胜收。",
    },
    {
        "id": uid("poem-026"),
        "title": "示儿",
        "author": "陆游",
        "dynasty": "宋",
        "content": "死去元知万事空，但悲不见九州同。王师北定中原日，家祭无忘告乃翁。",
        "content_lines": json.dumps(["死去元知万事空，", "但悲不见九州同。", "王师北定中原日，", "家祭无忘告乃翁。"], ensure_ascii=False),
        "annotation": json.dumps(["元知：原本知道。", "九州同：国家统一。", "乃翁：你的父亲。"], ensure_ascii=False),
        "translation": "我本来知道死后世间万事皆空，只是悲伤没有亲眼看到国家统一。当朝廷军队收复中原失地的那一天，你们举行家祭时千万别忘了把这个好消息告诉你们的父亲。",
        "background": "陆游临终前写给儿子的绝笔诗，表达至死不渝的爱国之情。",
        "difficulty": 2,
        "tags": "意象:九州,意象:家祭|主题:爱国,主题:遗嘱|场景:临终",
        "scene_type": "临终",
        "scene_desc": "陆游临终榻前，含泪嘱咐儿孙，至死不渝期盼中原收复。",
    },
    {
        "id": uid("poem-027"),
        "title": "小池",
        "author": "杨万里",
        "dynasty": "宋",
        "content": "泉眼无声惜细流，树阴照水爱晴柔。小荷才露尖尖角，早有蜻蜓立上头。",
        "content_lines": json.dumps(["泉眼无声惜细流，", "树阴照水爱晴柔。", "小荷才露尖尖角，", "早有蜻蜓立上头。"], ensure_ascii=False),
        "annotation": json.dumps(["泉眼：泉水的出口。", "晴柔：晴天里柔和的风光。", "尖尖角：初出水面的荷叶尖端。"], ensure_ascii=False),
        "translation": "泉眼悄然无声是因舍不得细细的水流，树荫倒映水面是喜爱晴天和风的轻柔。娇嫩的小荷叶刚从水面露出尖尖的角，早有一只调皮的小蜻蜓立在它的上头。",
        "background": "描写初夏池塘景色的田园诗，清新灵动。",
        "difficulty": 1,
        "tags": "意象:泉眼,意象:小荷,意象:蜻蜓|主题:夏日,主题:田园|场景:池塘",
        "scene_type": "池塘",
        "scene_desc": "初夏池塘，泉眼无声细流，小荷才露尖角，蜻蜓立上枝头。",
    },
    {
        "id": uid("poem-028"),
        "title": "竹石",
        "author": "郑燮",
        "dynasty": "清",
        "content": "咬定青山不放松，立根原在破岩中。千磨万击还坚劲，任尔东西南北风。",
        "content_lines": json.dumps(["咬定青山不放松，", "立根原在破岩中。", "千磨万击还坚劲，", "任尔东西南北风。"], ensure_ascii=False),
        "annotation": json.dumps(["咬定：比喻根扎得结实。", "破岩：破裂的岩石。", "坚劲：坚韧。"], ensure_ascii=False),
        "translation": "竹子紧紧咬定青山绝不放松，它的根原本就深扎在破裂的岩石中。经历成千上万次的折磨和打击依然坚韧挺拔，任凭你东西南北来的狂风。",
        "background": "郑板桥题画诗，以竹喻人，表达坚韧不屈的精神。",
        "difficulty": 2,
        "tags": "意象:竹,意象:青山,意象:风|主题:咏物,主题:坚韧|场景:山林",
        "scene_type": "山林",
        "scene_desc": "青山岩石间，翠竹咬定不放，任尔东西南北风，巍然不屈。",
    },
    {
        "id": uid("poem-029"),
        "title": "己亥杂诗",
        "author": "龚自珍",
        "dynasty": "清",
        "content": "浩荡离愁白日斜，吟鞭东指即天涯。落红不是无情物，化作春泥更护花。",
        "content_lines": json.dumps(["浩荡离愁白日斜，", "吟鞭东指即天涯。", "落红不是无情物，", "化作春泥更护花。"], ensure_ascii=False),
        "annotation": json.dumps(["浩荡：广大。", "吟鞭：诗人的马鞭。", "落红：落花。"], ensure_ascii=False),
        "translation": "满怀离愁对着夕阳西下，扬鞭东去从此浪迹天涯。凋落的花瓣并非无情之物，它化作春天的泥土更能滋养新的花朵。",
        "background": "龚自珍辞官南归途中作，以落花自喻，表现虽脱离官场仍关心国家命运。",
        "difficulty": 3,
        "tags": "意象:落红,意象:春泥,意象:白日|主题:离别,主题:奉献|场景:归途",
        "scene_type": "归途",
        "scene_desc": "夕阳西下，诗人策马东行，落花化作春泥，孕育新的希望。",
    },
    {
        "id": uid("poem-030"),
        "title": "村居",
        "author": "高鼎",
        "dynasty": "清",
        "content": "草长莺飞二月天，拂堤杨柳醉春烟。儿童散学归来早，忙趁东风放纸鸢。",
        "content_lines": json.dumps(["草长莺飞二月天，", "拂堤杨柳醉春烟。", "儿童散学归来早，", "忙趁东风放纸鸢。"], ensure_ascii=False),
        "annotation": json.dumps(["拂堤：杨柳枝条拂掠堤岸。", "春烟：春天水泽草木蒸发的水汽。", "纸鸢：风筝。"], ensure_ascii=False),
        "translation": "农历二月青草生长黄莺飞舞，杨柳枝条轻拂堤岸沉醉在春天的雾气中。村里的孩子们放学后急急忙忙跑回家，趁着东风把风筝放上蓝天。",
        "background": "描写早春二月乡村儿童放风筝的生活场景。",
        "difficulty": 1,
        "tags": "意象:草,意象:莺,意象:风筝|主题:春景,主题:童趣|场景:乡村",
        "scene_type": "乡村",
        "scene_desc": "二月春光，杨柳拂堤，草长莺飞，孩童趁着东风放飞纸鸢。",
    },
]

# ============================================================
# 节日数据（20条）
# ============================================================

FESTIVALS = [
    {
        "id": uid("festival-001"),
        "name": "春节",
        "date_rule": "L:01-01",
        "poem_tags": "主题:春节,主题:迎新|场景:春节",
        "event_level": "L1",
        "description": "农历新年，中国最重要的传统节日",
    },
    {
        "id": uid("festival-002"),
        "name": "元宵节",
        "date_rule": "L:01-15",
        "poem_tags": "主题:元宵,主题:团圆|场景:上元",
        "event_level": "L2",
        "description": "正月十五，赏花灯、吃元宵",
    },
    {
        "id": uid("festival-003"),
        "name": "清明节",
        "date_rule": "S:清明",
        "poem_tags": "主题:清明,主题:思乡,主题:踏青|场景:清明",
        "event_level": "L2",
        "description": "扫墓祭祖、踏青游春",
    },
    {
        "id": uid("festival-004"),
        "name": "端午节",
        "date_rule": "L:05-05",
        "poem_tags": "主题:端午,主题:爱国|场景:端午",
        "event_level": "L2",
        "description": "纪念屈原，赛龙舟、吃粽子",
    },
    {
        "id": uid("festival-005"),
        "name": "七夕",
        "date_rule": "L:07-07",
        "poem_tags": "主题:爱情,主题:七夕|场景:七夕",
        "event_level": "L3",
        "description": "牛郎织女鹊桥相会，中国情人节",
    },
    {
        "id": uid("festival-006"),
        "name": "中秋节",
        "date_rule": "L:08-15",
        "poem_tags": "意象:月,意象:团圆|主题:中秋,主题:思乡|场景:中秋",
        "event_level": "L1",
        "description": "赏月、吃月饼，阖家团圆",
    },
    {
        "id": uid("festival-007"),
        "name": "重阳节",
        "date_rule": "L:09-09",
        "poem_tags": "主题:重阳,主题:登高,主题:思乡|场景:重阳",
        "event_level": "L3",
        "description": "登高望远、赏菊、敬老",
    },
    {
        "id": uid("festival-008"),
        "name": "冬至",
        "date_rule": "S:冬至",
        "poem_tags": "主题:冬至,主题:思乡|场景:冬至",
        "event_level": "L3",
        "description": "一年中白昼最短的一天，北方吃饺子南方吃汤圆",
    },
    {
        "id": uid("festival-009"),
        "name": "腊八节",
        "date_rule": "L:12-08",
        "poem_tags": "主题:腊八,主题:年味|场景:腊八",
        "event_level": "L4",
        "description": "喝腊八粥，拉开过年序幕",
    },
    {
        "id": uid("festival-010"),
        "name": "元旦",
        "date_rule": "G:01-01",
        "poem_tags": "主题:新年,主题:迎新|场景:元旦",
        "event_level": "L2",
        "description": "公历新年",
    },
    {
        "id": uid("festival-011"),
        "name": "春分",
        "date_rule": "G:03-21",
        "poem_tags": "意象:春|主题:节气,主题:春景|场景:春分",
        "event_level": "L4",
        "event_sub_type": "nature",
        "description": "昼夜平分，春意渐浓",
    },
    {
        "id": uid("festival-012"),
        "name": "母亲节",
        "date_rule": "G:05-10",
        "poem_tags": "主题:母爱,主题:感恩|场景:母亲节",
        "event_level": "L3",
        "event_sub_type": "emotion",
        "description": "感恩母亲的节日",
    },
    {
        "id": uid("festival-013"),
        "name": "父亲节",
        "date_rule": "G:06-15",
        "poem_tags": "主题:父爱,主题:感恩|场景:父亲节",
        "event_level": "L4",
        "event_sub_type": "emotion",
        "description": "感恩父亲的节日",
    },
    {
        "id": uid("festival-014"),
        "name": "教师节",
        "date_rule": "G:09-10",
        "poem_tags": "主题:感恩,主题:师恩|场景:教师节",
        "event_level": "L4",
        "event_sub_type": "culture",
        "description": "感谢教师的辛勤付出",
    },
    {
        "id": uid("festival-015"),
        "name": "国庆节",
        "date_rule": "G:10-01",
        "poem_tags": "主题:爱国,主题:国庆|场景:国庆",
        "event_level": "L1",
        "description": "庆祝中华人民共和国成立",
    },
    {
        "id": uid("festival-016"),
        "name": "世界读书日",
        "date_rule": "G:04-23",
        "poem_tags": "主题:读书,主题:求知|场景:读书",
        "event_level": "L4",
        "event_sub_type": "culture",
        "description": "鼓励阅读和写作",
    },
    {
        "id": uid("festival-017"),
        "name": "除夕",
        "date_rule": "L:12-30",
        "poem_tags": "主题:除夕,主题:团圆,主题:辞旧|场景:除夕",
        "event_level": "L1",
        "description": "岁末最后一天，阖家团圆守岁",
    },
    {
        "id": uid("festival-018"),
        "name": "中秋·望月怀远",
        "date_rule": "S:立秋",
        "poem_tags": "意象:秋,意象:月|主题:立秋,主题:秋思|场景:立秋",
        "event_level": "L4",
        "event_sub_type": "nature",
        "description": "秋季开始，暑去凉来",
    },
    {
        "id": uid("festival-019"),
        "name": "小年",
        "date_rule": "L:12-23",
        "poem_tags": "主题:小年,主题:年俗|场景:小年",
        "event_level": "L4",
        "event_sub_type": "culture",
        "description": "祭灶、扫尘，年味渐浓",
    },
    {
        "id": uid("festival-020"),
        "name": "七夕·鹊桥仙",
        "date_rule": "G:08-04",
        "poem_tags": "主题:爱情,主题:相思|场景:七夕",
        "event_level": "L4b",
        "event_sub_type": "emotion",
        "description": "牛郎织女相会，千古爱情传说",
    },
]

# ============================================================
# 课本数据
# ============================================================

TEXTBOOK_ID = uid("textbook-001")
POEM_TEXTBOOKS = [
    {"poem_id": uid("poem-001"), "grade": 7, "semester": "upper", "unit": 1, "teaching_focus": "思乡诗"},
    {"poem_id": uid("poem-002"), "grade": 7, "semester": "upper", "unit": 1, "teaching_focus": "春景诗"},
    {"poem_id": uid("poem-003"), "grade": 7, "semester": "upper", "unit": 2, "teaching_focus": "哲理诗"},
    {"poem_id": uid("poem-004"), "grade": 7, "semester": "upper", "unit": 1, "teaching_focus": "咏物启蒙"},
    {"poem_id": uid("poem-005"), "grade": 7, "semester": "upper", "unit": 2, "teaching_focus": "悯农诗"},
    {"poem_id": uid("poem-006"), "grade": 7, "semester": "upper", "unit": 3, "teaching_focus": "写景诗豪放"},
    {"poem_id": uid("poem-011"), "grade": 7, "semester": "upper", "unit": 3, "teaching_focus": "边塞诗"},
    {"poem_id": uid("poem-012"), "grade": 7, "semester": "upper", "unit": 3, "teaching_focus": "边塞诗爱国"},
    {"poem_id": uid("poem-015"), "grade": 7, "semester": "upper", "unit": 4, "teaching_focus": "送别诗"},
    {"poem_id": uid("poem-021"), "grade": 7, "semester": "upper", "unit": 4, "teaching_focus": "送别诗友情"},
]

# 今日推荐诗词（仅1条置顶推荐，换一首由API动态创建）
DAILY_TODAY_POEM_ID = uid("poem-001")
DAILY_TODAY_REASON = "经典咏流传，李白望月思故乡"


async def seed_database():
    """执行种子数据初始化"""

    # 1. 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 2. 检查诗词是否已存在
        result = await db.execute(select(Poem).limit(1))
        if result.scalar_one_or_none():
            print("[Seed] 诗词数据已存在，跳过种子初始化。")
            return

        print("[Seed] 开始插入种子数据...")

        # 3. 插入诗词
        for p in POEMS:
            poem = Poem(**p)
            db.add(poem)
        await db.flush()
        print(f"[Seed] 已插入 {len(POEMS)} 首诗词。")

        # 4. 插入节日
        for f in FESTIVALS:
            festival = Festival(**f)
            db.add(festival)
        await db.flush()
        print(f"[Seed] 已插入 {len(FESTIVALS)} 条节日数据。")

        # 5. 插入课本
        textbook = Textbook(
            id=TEXTBOOK_ID,
            name="人教版（统编版）",
            publisher="人民教育出版社",
            edition="2024年版",
        )
        db.add(textbook)
        await db.flush()

        for pt in POEM_TEXTBOOKS:
            poem_textbook = PoemTextbook(
                id=uid(f"ptb-{pt['poem_id']}-{pt['grade']}{pt['semester']}"),
                poem_id=pt["poem_id"],
                textbook_id=TEXTBOOK_ID,
                grade=pt["grade"],
                semester=pt["semester"],
                unit=pt["unit"],
                teaching_focus=pt["teaching_focus"],
            )
            db.add(poem_textbook)
        print(f"[Seed] 已插入 1 条课本和 {len(POEM_TEXTBOOKS)} 条课本关联。")

        # 6. 生成今日推荐（1条置顶，换一首由API动态创建）
        today = date.today()
        rec = DailyRecommendation(
            id=uid(f"daily-{today.isoformat()}-pinned"),
            poem_id=DAILY_TODAY_POEM_ID,
            recommend_date=today,
            reason=DAILY_TODAY_REASON,
            reason_type="manual",
            matched_tags=None,
            is_pinned=True,
        )
        db.add(rec)
        print("[Seed] 已插入 1 条今日推荐（置顶）。")

        await db.commit()
        print("[Seed] 种子数据初始化完成！")


async def main():
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
