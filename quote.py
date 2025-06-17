import streamlit as st
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import uuid

# streamlit run D:\Project\工具\quote\quote.py
# streamlit run D:\Project\工具\quote\1.py

# --- 数据库设置 ---
Base = declarative_base()

# 定义报价单模型（数据库表）
class Quote(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_number = Column(String, unique=True, nullable=False)  # 唯一标识报价单
    client_name = Column(String, nullable=False)
    quote_date = Column(Date, nullable=False)
    items = Column(JSON, nullable=False)  # 使用JSON存储商品项
    shipping_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    shipping_time = Column(String, nullable=False)  # 运输时长
    shipping_method = Column(String, nullable=False)  # 运输方式
    remarks = Column(String, nullable=True)  # 备注
    discount = Column(Float, nullable=False, default=0.0)  # 折扣

# 创建 SQLite 数据库（如果数据库存在则连接）
engine = create_engine('sqlite:///quotes.db', echo=True)

# 创建表（如果是第一次运行，可以取消下行的注释）
# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# 创建与数据库交互的 session
Session = sessionmaker(bind=engine)
session = Session()

# --- 保存报价记录到数据库的函数 ---
def save_quote_to_db(client_name, quote_date, items, shipping_cost, total_cost, shipping_time, shipping_method, remarks, discount):
    # 生成唯一的报价单编号（UUID）
    quote_number = str(uuid.uuid4())

    # 创建一个新的报价单实例，并加入到会话中
    quote = Quote(
        quote_number=quote_number,
        client_name=client_name,
        quote_date=quote_date,
        items=json.dumps(items),  # 将商品列表转换为 JSON 字符串
        shipping_cost=shipping_cost,
        total_cost=total_cost,
        shipping_time=shipping_time,
        shipping_method=shipping_method,
        remarks=remarks,
        discount=discount
    )

    try:
        session.add(quote)  # 将报价单加入到会话中
        session.commit()  # 提交事务，保存到数据库
        return quote_number
    except Exception as e:
        session.rollback()  # 出现错误时回滚事务
        st.error(f"保存报价单时出错: {e}")
        return None

# --- 查询报价单的函数 ---
def get_quote_by_number(quote_number):
    try:
        # 查询特定报价单号的报价记录
        quote = session.query(Quote).filter_by(quote_number=quote_number).first()
        if quote:
            # 输出报价单信息
            st.write(f"**报价单号**: {quote.quote_number}")
            st.write(f"**客户姓名**: {quote.client_name}")
            st.write(f"**报价日期**: {quote.quote_date}")
            st.write(f"**商品明细**: {json.loads(quote.items)}")  # 转换 JSON 字符串为 Python 对象
            st.write(f"**运费**: ${quote.shipping_cost:.2f}")
            st.write(f"**总费用**: ${quote.total_cost:.2f}")
            st.write(f"**运输时长**: {quote.shipping_time}")
            st.write(f"**运输方式**: {quote.shipping_method}")
            st.write(f"**备注**: {quote.remarks}")
            st.write(f"**折扣**: {quote.discount * 100}%")
        else:
            st.warning("未找到该报价单号！")
    except Exception as e:
        st.error(f"查询报价单时出错: {e}")

def get_quotes_by_client_name(client_name):
    try:
        # 查询某个客户的所有报价单记录
        quotes = session.query(Quote).filter_by(client_name=client_name).all()
        if quotes:
            for quote in quotes:
                st.write(f"**报价单号**: {quote.quote_number}")
                st.write(f"**客户姓名**: {quote.client_name}")
                st.write(f"**报价日期**: {quote.quote_date}")
                st.write(f"**商品明细**: {json.loads(quote.items)}")  # 转换 JSON 字符串为 Python 对象
                st.write(f"**运费**: ${quote.shipping_cost:.2f}")
                st.write(f"**总费用**: ${quote.total_cost:.2f}")
                st.write(f"**运输时长**: {quote.shipping_time}")
                st.write(f"**运输方式**: {quote.shipping_method}")
                st.write(f"**备注**: {quote.remarks}")
                st.write(f"**折扣**: {quote.discount * 100}%")
                st.write("---")  # 分隔不同报价单
        else:
            st.warning(f"未找到客户 {client_name} 的报价单！")
    except Exception as e:
        st.error(f"查询报价单时出错: {e}")

# --- 价格计算函数 ---
def calculate_price(cost_price, promotion_rate, tariff_rate, accessories_cost, quantity):

    # 固定值
    insurance_fee_rate = 0.03
    profit_margin = 0.3
    exchange_rate = 7.2

    insurance_fee = cost_price * insurance_fee_rate
    promotion = cost_price * promotion_rate
    tariff = cost_price * tariff_rate

    total_cost = cost_price + insurance_fee + promotion + tariff + accessories_cost
    cny_unit_price = total_cost * (1 + profit_margin)
    usd_unit_price = cny_unit_price / exchange_rate
    usd_total_price = usd_unit_price * quantity if quantity > 0 else 0
    usd_unit_kg = quantity * 0.02

    # 返回计算结果
    return {
        "总采购成本": round(total_cost, 4),
        "人民币总价": round(cny_unit_price, 4),
        "美元单价": round(usd_unit_price, 4),
        "美元总价": round(usd_total_price, 4) if quantity >= 0 else "-",
        "预估重量": round(usd_unit_kg, 4),
    }

# --- Streamlit UI ---
st.set_page_config(page_title="报价系统", layout="wide")
st.title("🧮 报价系统 (Quotation Tool)")

st.markdown(
    "此工具用于快速计算商品总成本与售价，并生成专业报价单。\n\n**固定值：**\n- 汇率: 7.2\n- 信保手续费: 3%\n- 利润率: 30%")

# --- 核价计算区 ---
st.subheader("🧾 核价计算区")
col1, col2, col3 = st.columns(3)

with col1:
    cost_price = st.number_input("采购成本 (元)", value=0.0, step=0.01, key="cost_price")
    promotion_rate = st.number_input("促销折扣 (%)", value=0.0, step=0.1, key="promotion_rate") / 100

with col2:
    tariff_rate = st.number_input("关税 (%)", value=0.0, step=0.1, key="tariff_rate") / 100
    accessories_cost = st.number_input("配件成本 (元)", value=0.0, step=0.1, key="accessories_cost")

with col3:
    quantity = st.number_input("件数", value=0.0, step=1.0, key="quantity")

if st.button("📊 开始计算"):
    result = calculate_price(cost_price, promotion_rate, tariff_rate, accessories_cost, quantity)
    st.subheader("📈 计算结果：")
    for label, value in result.items():
        st.write(f"**{label}**: {value:.2f}")
else:
    st.info("请填写所有必填项并点击“开始计算”按钮。")

# 客户信息输入
st.subheader("📋 客户信息与商品明细")
col1, col2 = st.columns(2)

with col1:
    client_name = st.text_input("客户姓名", value="")
with col2:
    quote_date = st.date_input("报价日期", value=date.today())

# 商品条目数
item_count = st.number_input("商品项数 (行数)", min_value=1, max_value=20, step=1, value=1, key="item_count")
items = []

st.subheader("📦 商品明细")
st.markdown("常用规格：\n"
            "\n- Double side clear print,cnc diamond cut,thickness>3.5MM,40designs x 25pcs"
            "\n- Single side epoxy,cnc diamond cut,thickness>3.5MM"
            "\n- Double sided print, laser cut, 2designs"
            )

for i in range(int(item_count)):
    with st.container():
        st.markdown(
            f"<div style='background-color:#f9f9f9;padding:10px 15px;border:1px solid #ccc;border-radius:10px;margin-bottom:10px'>",
            unsafe_allow_html=True)
        cols = st.columns([2, 3, 1.5, 1, 1, 1])
        with cols[0]:
            item_options = ["Acrylic keychain", "Mini CD Keychain", "Fridge Magnet", "Button Pin Badge",
                            "Shaker Keychain","Acrylic Standee","Acrylic Pin", "Phone Grips", "Paper Clips"]
            item = st.selectbox(f"Item_{i}", item_options, key=f"item_{i}")
        with cols[1]:
            spec = st.text_input(f"Specifications_{i}", key=f"spec_{i}")
        with cols[2]:
            size = st.text_input(f"Size_{i}", key=f"size_{i}")
        with cols[3]:
            qty = st.number_input(f"Qty_{i}", key=f"qty_{i}", value=0)
        with cols[4]:
            unit_price = st.number_input(f"Unit price($)_{i}", key=f"price_{i}", value=0.0, format="%.2f")
        total_price = qty * unit_price
        with cols[5]:
            st.markdown(f"**${total_price:.2f}**")
        st.markdown("</div>", unsafe_allow_html=True)

        items.append({
            "Item": item,
            "Specifications": spec,
            "Size": size,
            "Qty": qty,
            "Unit price($)": unit_price,
            "Total price($)": total_price
        })

# 运费输入
st.markdown("---")
shipping_method = st.text_input("运输方式 (Shipping Method)", value="")  # 用户输入运输方式
shipping_cost = st.number_input("运费 Shipping cost ($)", value=0.0, step=0.01, format="%.2f", key="shipping_cost")
shipping_time = st.text_input("运输时长 (Shipping Time, e.g., 4-7 working days)", value="4-7 working days")
remarks = st.text_area("备注 (Optional)", value="")  # 备注

# 汇总计算
subtotal = sum(item["Total price($)"] for item in items)
discounted_subtotal = subtotal * 0.9  # 9折的折扣

# 更新total_cost为折扣后的总价 + 运费
total_cost = discounted_subtotal + shipping_cost

# 报价单预览
st.markdown("---")
st.subheader("📊 报价单预览")

# 显示商品明细
quote_content = ""
# 显示客户信息
quote_content += f"\n{client_name}\n{quote_date}\n\n"

for i, item in enumerate(items):
    quote_content += f"Item {i + 1}: {item['Item']}\n"
    quote_content += f"Specifications: {item['Specifications']}\n"
    quote_content += f"Size: {item['Size']}\n"
    quote_content += f"Quantity (Pieces): {item['Qty']}\n"
    quote_content += f"Unit Price: ${item['Unit price($)']:.2f}\n"
    quote_content += f"Total Price: ${item['Total price($)']:.2f}\n"

quote_content += f"New Customer (with 10% discount): ${discounted_subtotal:.2f}\n"  # 显示折扣后的价格
quote_content += f"Shipping cost ({shipping_time}): ${shipping_cost:.2f}\n"
quote_content += f"Total cost: ${total_cost:.2f}\n"
# quote_content += f"Shipping Method: {shipping_method}\n"
# quote_content += f"Remarks: {remarks}\n"  # 显示备注

# 复制报价单按钮
st.text_area("📋 复制报价单", quote_content, height=400, key="quote_copy")

# 保存报价记录到数据库
if st.button("Save Quote to Database"):
    if client_name and len(items) > 0:
        quote_number = save_quote_to_db(client_name, quote_date, items, shipping_cost, total_cost, shipping_time, shipping_method, remarks, 0.1)
        if quote_number:
            st.success(f"报价已保存！报价单编号：{quote_number}")
    else:
        st.error("请填写所有必填项！")

# 查询报价单区
st.markdown("---")
st.subheader("🔍 查询报价单")

quote_search_type = st.radio("查询方式", ["按报价单号查询", "按客户姓名查询"])

if quote_search_type == "按报价单号查询":
    quote_number_to_search = st.text_input("请输入报价单号查询", value="")
    if st.button("查询"):
        if quote_number_to_search:
            get_quote_by_number(quote_number_to_search)
        else:
            st.error("请输入报价单号！")

elif quote_search_type == "按客户姓名查询":
    client_name_to_search = st.text_input("请输入客户姓名查询", value="")
    if st.button("查询"):
        if client_name_to_search:
            get_quotes_by_client_name(client_name_to_search)
        else:
            st.error("请输入客户姓名！")


# streamlit run C:\Users\可可西\Desktop\quote.py

# streamlit run D:\project\project0107\工具\报价工具\hy.py
import streamlit as st
import requests
import json
import pandas as pd

# 国家名称 -> 二字编码映射（部分示例，完整列表可补充）
country_map = {
    "美国": "US",
    "加拿大": "CA",
    "德国": "DE",
    "法国": "FR",
    "日本": "JP",
    "澳大利亚": "AU",
    "中国香港": "HK",
    "英国": "GB",
    "意大利": "IT",
    "越南": "VN",
    "泰国": "TH",
    "印度": "IN",
    "马来西亚": "MY",
    "菲律宾": "PH",
    "印尼": "ID",
    "韩国": "KR",
    "新加坡": "SG",
    "阿尔巴尼亚": "AL",
    "奥地利": "AT",
    "白俄罗斯": "BY",
    "保加利亚": "BG",
    "比利时": "BE",
    "冰岛": "IS",
    "波兰": "PL",
    "丹麦": "DK",
    "俄罗斯": "RU",
    "芬兰": "FI",
    "荷兰": "NL",
    "立陶宛": "LT",
    "列支敦士登": "LI",
    "卢森堡": "LU",
    "罗马尼亚": "RO",
    "马耳他": "MT",
    "摩尔多瓦": "MD",
    "摩纳哥": "MC",
    "挪威": "NO",
    "葡萄牙": "PT",
    "圣马力诺": "SM",
    "斯洛文尼亚": "SI",
    "乌克兰": "UA",
    "西班牙": "ES",
    "希腊": "GR",
    "匈牙利": "HU",
    "巴基斯坦": "PK",
    "朝鲜": "KP",
    "老挝": "LA",
    "马尔代夫": "MV",
    "蒙古": "MN",
    "孟加拉国": "BD",
    "缅甸": "MM",
    "尼泊尔": "NP",
    "斯里兰卡": "LK",
    "文莱": "BN",
    "乌兹别克斯坦": "UZ",
    "阿富汗": "AF",
    "阿拉伯联合酋长国": "AE",
    "阿曼": "OM",
    "巴林": "BH",
    "格鲁吉亚": "GE",
    "哈萨克斯坦": "KZ",
    "卡塔尔": "QA",
    "科威特": "KW",
    "黎巴嫩": "LB",
    "塞浦路斯": "CY",
    "沙特阿拉伯": "SA",
    "塔吉克斯坦": "TJ",
    "土耳其": "TR",
    "土库曼斯坦": "TM",
    "叙利亚": "SY",
    "亚美尼亚": "AM",
    "伊拉克": "IQ",
    "伊朗": "IR",
    "以色列": "IL",
    "阿根廷": "AR",
    "巴拉圭": "PY",
    "巴西": "BR",
    "厄瓜多尔": "EC",
    "哥伦比亚": "CO",
    "圭亚那": "GY",
    "秘鲁": "PE",
    "苏里南": "SR",
    "委内瑞拉": "VE",
    "乌拉圭": "UY",
    "新西兰": "NZ"
}

# 设置页面标题
st.title("HY 物流运费查询")

# 选择国家（显示中文名称）
selected_country_name = st.selectbox("选择目的国家", list(country_map.keys()))
country_code = country_map[selected_country_name]

# 用户输入重量
weight = st.text_input("请输入包裹重量 (kg)", "1")

# 固定汇率
exchange_rate = 7.3

# 查询按钮
if st.button("查询运费"):
    try:
        url = "http://order.hy-express.com/webservice/PublicService.asmx/ServiceInterfaceUTF8"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {
            "appToken": "3f7e28f91fe9012a8cf511673228d5b6",
            "appKey": "a68b54a8852c481d00ad92625da6a6e8a68b54a8852c481d00ad92625da6a6e8",
            "serviceMethod": "feetrail",
            "paramsJson": json.dumps({
                "country_code": country_code,
                "weight": weight
            })
        }

        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        get_data = json.loads(response.text).get("data", [])

        if get_data:
            result_list = []
            for data in get_data:
                total_fee = float(data.get("TotalFee", 0))
                total_fee_usd = round(total_fee / exchange_rate, 2)
                result_list.append({
                    "运输方式": data.get("ServiceCnName", ""),
                    "运输时效": data.get("Effectiveness", ""),
                    "计费重量 (kg)": data.get("ChargeWeight", ""),
                    "总费用 (RMB)": f"{total_fee:.2f}",
                    "总费用 (USD)": f"{total_fee_usd:.2f}"
                })

            df = pd.DataFrame(result_list)
            st.success("查询成功")
            st.dataframe(df)
        else:
            st.warning("未获取到物流数据，请稍后重试。")

    except Exception as e:
        st.error(f"查询失败：{e}")
