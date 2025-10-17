from twitchio.ext import commands
from keep_alive import keep_alive
import random
import time
import os
import asyncio
import gspread  # 新增
import json     # 新增

# 儲存遊戲狀態
games = {}
# 記錄每個使用者上次發言的時間
last_message_time = {}
# 終極密碼冷卻時間紀錄
ultimate_cooldowns = {}
# 2A1B冷卻時間紀錄
two_a_one_b_cooldowns = {}
# 使用者紀錄
users = {}
# 冷卻時間設定
COOLDOWN_TIME = 5  # 每人 5 秒 CD
# 使用者開關
useropen ={}

# app.py 頂部或其他設定區塊
CHANNEL_COL = 1      # 頻道名稱 (A 欄)
NACHI_COUNT_COL = 2  # 娜奇計數 (B 欄)
NASHANAGI_COUNT_COL = 3 # 娜吉計數 (C 欄) 
COUNT_KEY = "Nachi_Count" # 定義計數的名稱 (如果 B1 是這個標題)

# 檢查是否允許發言
def can_send_message(username):
    now = time.time()
    if username not in last_message_time:
        last_message_time[username] = now
        return True
    # 若距離上次發言 >= 5 秒，就允許
    if now - last_message_time[username] > 3:
        last_message_time[username] = now
        return True
    return False

CHANNEL1 = "ichihatsuhane"   # 你的頻道帳號
CHANNEL2 = "datura_cherish"  # 你的頻道帳號
CHANNEL3 = "bcatshanachie"   # 你的頻道帳號
CHANNEL4 = "1268735151431"   # 你的頻道帳號
CHANNEL5 = "miobarbatos"     # 你的頻道帳號
CHANNEL6 = "justababu"

bot = commands.Bot(
    token=os.environ.get("TWITCH_TOKEN"),  # 請填入你的 ACCESS TOKEN
    prefix='!',
    initial_channels=[CHANNEL1,CHANNEL2,CHANNEL3,CHANNEL4,CHANNEL5,CHANNEL6]
)


@bot.command(name="呼吸", aliases=["氧氣瓶","拔管","斷氣"])
async def oxygen_command(ctx):
    channel = ctx.channel.name
    people = get_user(channel, ctx.author.name)
    if not can_send_message(people['name']):
        try:
            await ctx.channel.send(f"/timeout {people['name']} 1")  # 刪除使用者的訊息
        except Exception as e:
            print(f"刪除訊息失敗: {e}")
        return

    value = random.randint(0, 100)  # 產生 0~100 的隨機整數
    await ctx.send(f"  {people['name']}  你的氧氣值目前是： {value}%")
    
# 小羽專區 Star  
@bot.command(name="小羽", aliases=["羽哥"])
async def ichihatsuhane_command(ctx):
    channel = ctx.channel.name
    get_user(channel, ctx.author.name)
    if channel.lower() == "ichihatsuhane":
        await ctx.send(" datura3LLOVE 看看喔~香雞翅~蒸菱角~不好吃不用錢喔~ datura3RLOVE ")
        
@bot.command(name="辣椒", aliases=["小狗"])
async def ochili_command(ctx):
    channel = ctx.channel.name
    get_user(channel, ctx.author.name)
    if channel.lower() == "ichihatsuhane":
        await ctx.send("  ichihaGood 是我們最敬愛最偉大最厲害最棒的 @ino_yuma_ ichihaGood ")
# 小羽專區 End
  
# 娜奇專區 Star
# --- Google Sheets 認證函式 ---
def get_gspread_client():
    # 從 Render 環境變數中讀取 JSON 憑證
    creds_json = os.environ.get("GSPREAD_CREDENTIALS")
    
    if not creds_json:
        print("❌ 致命錯誤：GSPREAD_CREDENTIALS 環境變數未設定！")
        return None
    
    try:
        # 將 JSON 字串轉換為 Python 字典
        creds_dict = json.loads(creds_json)
        
        # 使用字典中的憑證進行認證
        client = gspread.service_account_from_dict(creds_dict)
        print("✅ 成功初始化 Google Sheets 客戶端！")
        return client
    except Exception as e:
        # 關鍵錯誤輸出
        print(f"❌ 致命錯誤：Gspread client 認證失敗！請檢查 JSON 憑證格式。原始錯誤: {e}")
        return None
    
# 輔助函數：根據計數名稱，確定對應的欄位索引 (B 欄或 C 欄)
def get_column_index(count_type):
    if count_type == "nachi":
        return NACHI_COUNT_COL
    elif count_type == "nashanagi":
        return NASHANAGI_COUNT_COL
    return None

# 函數：讀取特定頻道的特定計數
def read_sheet_count(client, channel_name, count_type):
    col_index = get_column_index(count_type)
    if col_index is None: return 0

    try:
        sheet_id = os.environ.get("SPREADSHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        
        # 1. 查找頻道名稱 (忽略標題行 A1)
        # gspread 的 find 會從第一行開始，這可能導致它找到 A1 的 "Channel"
        # 我們手動指定從第二行開始找，但 gspread 的 find 預設會找遍整個範圍。
        # 更好的方法是使用 worksheet.col_values(CHANNEL_COL)[1:] 進行本地查找

        # 這裡我們依靠 worksheet.find，並假設它從第二行開始找實際數據
        channel_cell = worksheet.find(channel_name, in_column=CHANNEL_COL) 
        
        if channel_cell and channel_cell.row > 1: # 確保不是標題行 (A1)
            # 讀取該行對應欄位的值
            value_cell = worksheet.cell(channel_cell.row, col_index)
            value = value_cell.value
            
            # 確保讀取到的值是數字 (即使它是字串格式)
            if value:
                try:
                    return int(value)
                except ValueError:
                    print(f"警告: 讀取到非數字值 '{value}', 該計數將從 0 開始。")
                    return 0
            
        return 0 # 找不到頻道或計數值為空
    except Exception as e:
        print(f"❌ 致命錯誤：讀取 Google Sheets 失敗！原始錯誤: {e}")
        return 0

# 函數：寫入/更新特定頻道的特定計數
def write_sheet_count(client, channel_name, new_count, count_type):
    col_index = get_column_index(count_type)
    if col_index is None: return False

    try:
        sheet_id = os.environ.get("SPREADSHEET_ID")
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1

        # 1. 查找頻道所在的行 (A 欄)
        channel_cell = worksheet.find(channel_name, in_column=CHANNEL_COL)
        
        if channel_cell:
            # 2. 如果找到，更新該行對應欄位 (B 欄或 C 欄) 的值
            worksheet.update_cell(channel_cell.row, col_index, new_count)
        else:
            # 3. 找不到該頻道，則在表格末尾新增一行 
            # 創建一個長度為 NASHANAGI_COUNT_COL (即 3) 的列表
            new_row = ["" for _ in range(NASHANAGI_COUNT_COL)]
            new_row[CHANNEL_COL - 1] = channel_name # A 欄填入頻道名
            new_row[col_index - 1] = new_count # 對應的 B 或 C 欄填入計數值
            worksheet.append_row(new_row)
            
        print(f"✅ 成功更新 Google Sheet：{channel_name} - {count_type} -> {new_count}")

        return True
    except Exception as e:
        # 關鍵錯誤輸出
        print(f"❌ 致命錯誤：寫入 Google Sheets 失敗！原始錯誤: {e}")
        return False
# ------------------------------------ Google Sheets 持久化儲存區 End --------------------------------------
    
# 修復後的 !娜奇 指令
@bot.command(name="娜奇")
async def nachi_command(ctx):
    global gspread_client 
    channel_name = ctx.channel.name.lower()
    
    # 保持頻道限定 (如果需要的話，這裡可以移除限定，讓所有頻道都計數)
    if channel_name == "bcatshanachie":
        if gspread_client:
            # 【修正點】: 補上 count_type 參數 "nachi"
            count = read_sheet_count(gspread_client, channel_name, "nachi") + 1
            write_sheet_count(gspread_client, channel_name, count, "nachi")
            
            await ctx.send(f" 這是我們第 {count} 次呼喊娜奇了，臭肥宅聽到我們的呼喚了嗎？")
            
# 修復後的 !夏娜吉 指令 (確保邏輯完整)
@bot.command(name="夏娜吉")
async def nachiji_command(ctx):
    global gspread_client 
    channel_name = ctx.channel.name.lower()
    
    if channel_name == "bcatshanachie": # 保持原有的頻道限定
        if gspread_client:
            # 【修正點】: 補上 count_type 參數 "nashanagi"
            count = read_sheet_count(gspread_client, channel_name, "nashanagi") + 1
            write_sheet_count(gspread_client, channel_name, count, "nashanagi")
            
            await ctx.send(f" 這是我們第 {count} 次呼喊娜吉了，娜吉不要再叫了！！ bcatshChiwawa bcatshChiwawa ")
        
        
# 指令：新增或更新歷年獎勵
@bot.command(name="歷年獎勵添加")
async def add_rewards(ctx):
    channel = ctx.channel.name
    if channel.lower() == "bcatshanachie":
        people = get_user(channel, ctx.author.name)
        # 只允許台主新增
        if people['name'].lower() != channel.lower():
            await ctx.send(f"⚠️ {people['name']} 只有台主可以新增歷年獎勵！")
            return

        # 取得內容
        parts = ctx.message.content.strip().split(" ", 1)
        if len(parts) < 2:
            await ctx.send("⚠️ 使用方式： !歷年獎勵添加 <內容>")
            return
        content = parts[1]

        # 檔案路徑
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, f"{channel}.txt")

        # 寫入檔案（覆蓋）
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        await ctx.send(f"✅ {channel} 的歷年獎勵已更新完成！")

# 指令：讀取歷年訂閱獎勵
@bot.command(name="歷年訂閱獎勵")
async def read_rewards(ctx):
    channel = ctx.channel.name
    if channel.lower() == "bcatshanachie":

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, f"{channel}.txt")

        if not os.path.exists(file_path):
            await ctx.send(f"⚠️ {channel} 的歷年獎勵檔案不存在。")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if content:
            await ctx.send(content)
        else:
            await ctx.send(f"⚠️ {channel} 的歷年獎勵檔案是空的。")     
# 娜奇專區 End

#------------------------------------------------遊戲區---------------------------------------------------
async def end_game_after_timeout(channel, gametype="ultimate"):
    try:
        await asyncio.sleep(600)
        game = get_game(channel.name, gametype)
        if game["active"]:
            game["active"] = False
            reset_users(channel.name)
            await channel.send(f"⏰ 遊戲時間到！沒有人猜中，答案是 {game['answer']}")
    except asyncio.CancelledError:
        # 任務被取消，直接結束，不做任何事
        return
    
@bot.command(name="終極密碼開關")
async def ultimate_open(ctx):
    channel = ctx.channel.name
    people = get_user(channel, ctx.author.name)
    
    # 只有台主可以切換
    if people['name'].lower() != channel.lower() and people['name'].lower() != "1268735151431":
        await ctx.send(f"⚠️ 只有台主可以切換終極密碼開關！")
        return

    #解析指令是否有帶參數 Y 或 N
    parts = ctx.message.content.strip().split()
    choice = parts[1] if len(parts) > 1 else None

    status = game_usercanopen(channel, 'ultimate', choice)
    state_text = "開啟" if status else "關閉"
    await ctx.send(f"✅ 終極密碼遊戲一般觀眾開啟權限已 {state_text}！")

    
# 終極密碼遊戲
@bot.command(name="終極密碼")
async def ultimate_password(ctx):
    channel = ctx.channel.name
    now = time.time()
    # 如果該頻道沒有遊戲狀態，初始化
    game = get_game(channel, "ultimate")
        
    people = get_user(channel, ctx.author.name)
    
    # 確保使用者開關存在
    if channel not in useropen:
        useropen[channel] = {}
    if 'ultimate' not in useropen[channel]:
         useropen[channel]['ultimate'] = False  # 預設為 True
         
    # 解析是否有帶數字
    parts = ctx.message.content.strip().split(" ")
    has_number = len(parts) > 1

    # 🔹 只有台主可以開新遊戲（不帶數字時）
    if not has_number:
        #if people['name'].lower() != channel.lower() and people['name'].lower() != "1268735151431":
        #    await ctx.send(f" {people['name']} 只有台主才可以開新遊戲！")
        #    return
        if not useropen[channel]['ultimate']:
            if not ctx.author.is_mod and people['name'].lower() != channel.lower() and people['name'].lower() != "1268735151431":
                await ctx.send(f" {people['name']} 只有台主或 MOD 才可以開新遊戲！")
                return

    game = get_game(channel, "ultimate")


    # 沒有帶數字 → 開新遊戲
    if not has_number:
        if game["active"]:
            await ctx.send("⚠️ 已經有一場遊戲在進行！請輸入 !終極密碼 <數字> 來猜。")
            return

        game["active"] = True
        game["low"] = 0
        game["end"] = 50
        game["start_time"] = now
        people['times'] = 5  # 每個人初始5次機會
        game["timeout_task"] = asyncio.create_task(end_game_after_timeout(ctx.channel)) # 啟動自動結束協程
        if channel.lower() == "datura_cherish":
            game["high"] = 10000
            game["answer"] = random.randint(0, 10000)  # 阿糕的台頻道改成 0~10000
            await ctx.send(f" datura3Cute 終極密碼遊戲開始！請輸入 !終極密碼 <數字> 猜 0~10000 的數字。機會有{game['end']}次")
        else:
            game["high"] = 1000
            game["answer"] = random.randint(0, 1000)
            await ctx.send(f" datura3Cute 終極密碼遊戲開始！請輸入 !終極密碼 <數字> 猜 0~1000 的數字。機會有{game['end']}次")
        print(f"[{channel}] 終極密碼的答案是 {game['answer']}")
        return
    
    # 遊戲還沒開始或已經結束
    if not game.get("active", False):
        await ctx.send("⚠️ 目前沒有進行中的終極密碼遊戲，請先輸入 `終極密碼` 開始新的一場！")
        return

    # 遊戲還沒開始
    if not game["active"]:
        await ctx.send(" datura3Pitiful 遊戲尚未開始，請先輸入 !終極密碼 開始新遊戲。")
        print (game)
        return

    # 🔹 檢查冷卻時間(每個人CD分開)
    #if people['name'] in ultimate_cooldowns and now - ultimate_cooldowns[people['name']] < COOLDOWN_TIME:
    #    remaining = int(COOLDOWN_TIME - (now - ultimate_cooldowns[people['name']]))
    #    await ctx.send(f" {people['name']} ⏳ 指令冷卻中，請再等 {remaining} 秒！")
    #    return
    #ultimate_cooldowns[people['name']] = now  # 更新使用時間
    
    # 🔹 檢查冷卻時間(聊天室共用CD)
    if game["active"] and channel in ultimate_cooldowns and now - ultimate_cooldowns[channel] < COOLDOWN_TIME:
        remaining = int(COOLDOWN_TIME - (now - ultimate_cooldowns[channel]))
        await ctx.send(f"⏳ {people['name']} 指令冷卻中，請再等 {remaining} 秒！")
        return
    ultimate_cooldowns[channel] = now  # 更新使用時間

    # 嘗試解析數字
    try:
        guess = int(ctx.message.content.split(" ")[1])
    except (IndexError, ValueError):
        await ctx.send("請輸入正確格式： !終極密碼 <數字> datura3Attack ")
        return

    # 檢查範圍
    if guess <= game["low"] or guess >= game["high"]:
        await ctx.send(f" {people['name']} ，你的數字不在範圍內！ datura3Smelly 目前範圍是 {game['low']} ~ {game['high']} datura3Bonk")
        return

    # 猜對
    if guess == game["answer"] and people['times'] != 0:
        await ctx.send(f" bcatshYahoo 恭喜 {people['name']} 猜中！答案就是 {game['answer']} bcatshYahoo ")
        if channel == "justababu":
            await ctx.send(f"!addpoints {people['name']} 500")
        end_game(channel, "ultimate")
        reset_users(ctx.channel.name)
        if "timeout_task" in game:
            game["timeout_task"].cancel()
        return

    # 更新範圍
    if people['times'] == 0:
        await ctx.send(f"❌ {people['name']} 你沒有猜的機會了！請等待下一局遊戲開始。")
    else:
        if guess < game["answer"]:
            game["low"] = guess
            game["end"] = game["end"] - 1
            people['times'] = people['times'] - 1
            await ctx.send(f"⬆️ {people['name']} 猜 {guess} 太小了！範圍變更為 {game['low']} ~ {game['high']}。總剩餘 {game['end']} 次，你剩下 {people['times']} 次機會")
        else:
            game["high"] = guess
            game["end"] = game["end"] - 1
            people['times'] = people['times'] - 1
            await ctx.send(f"⬇️ {people['name']} 猜 {guess} 太大了！範圍變更為 {game['low']} ~ {game['high']}。總剩餘 {game['end']} 次，你剩下 {people['times']} 次機會")
    #次數歸0
    if game["end"] == 0:
        end_game(channel, "ultimate")
        reset_users(ctx.channel.name)
        await ctx.send(f"❌ 遊戲結束！沒有人猜中，答案是 {game['answer']}。 datura3Leave  datura3Leave ")
        if "timeout_task" in game:
            game["timeout_task"].cancel()
        return

# 結束遊戲指令
@bot.command(name="終極密碼結束")
async def end_ultimate(ctx):
    channel = ctx.channel.name
    people = get_user(channel, ctx.author.name)

    # 確保遊戲存在
    if channel not in games or not games[channel]["active"]:
        await ctx.send("❌ 目前沒有進行中的終極密碼遊戲。")
        return

    # 只有台主或特定使用者可以結束遊戲
    if people['name'].lower() != channel.lower() and people['name'].lower() != "1268735151431":
        await ctx.send(f"⚠️ {people['name']} 只有台主才可以結束遊戲！")
        return

    answer = games[channel]["answer"]
    games[channel]["active"] = False
    reset_users(ctx.channel.name)
    if "timeout_task" in games[channel]:
        games[channel]["timeout_task"].cancel()
    await ctx.send(f"🛑 終極密碼遊戲已被結束！答案是 {answer}。")

#2A1B遊戲

# 生成不重複 4 位數字
def generate_answer():
    digits = list("0123456789")
    random.shuffle(digits)
    return "".join(digits[:4])

# 計算 A 和 B
def calculate_ab(answer, guess):
    A = sum(a==b for a,b in zip(answer, guess))
    B = sum(min(answer.count(d), guess.count(d)) for d in guess) - A
    return A, B

@bot.command(name="2A1B開關")
async def two_a_one_b_open(ctx):
    channel = ctx.channel.name
    people = get_user(channel, ctx.author.name)
    
    # 只有台主可以切換
    if people['name'].lower() != channel.lower() and people['name'].lower() != "1268735151431":
        await ctx.send(f"⚠️ 只有台主可以切換'2A1B'開關！")
        return

    #解析指令是否有帶參數 Y 或 N
    parts = ctx.message.content.strip().split()
    choice = parts[1] if len(parts) > 1 else None

    status = game_usercanopen(channel, '2A1B', choice)
    state_text = "開啟" if status else "關閉"
    await ctx.send(f"✅ '2A1B'遊戲一般觀眾開啟權限已 {state_text}！")
    
    
    
@bot.command(name="2A1B")
async def two_a_one_b(ctx):
    channel = ctx.channel.name
    people = get_user(channel, ctx.author.name)
    now = time.time()
    game = get_game(channel, "2A1B")
    
    # 確保使用者開關存在
    if channel not in useropen:
        useropen[channel] = {}
    if '2A1B' not in useropen[channel]:
         useropen[channel]['2A1B'] = False  # 預設為 False
         
    # 解析是否有帶數字
    parts = ctx.message.content.strip().split(" ")
    has_number = len(parts) > 1
    
    # 🔹 預設只有台主可以開新遊戲（不帶數字時）
    if not has_number:
        if not useropen[channel]['2A1B']:
            if not ctx.author.is_mod and people['name'].lower() != channel.lower() and people['name'].lower() != "1268735151431":
                await ctx.send(f" {people['name']} 只有台主或 MOD 才可以開新遊戲！")
                return
    # 初始化遊戲
    if not has_number:
        if game.get("active", False):
            await ctx.send("⚠️ 已經有一場遊戲在進行！請輸入 !2A1B <數字> 來猜。")
            return

        game["active"] = True
        game["answer"] = generate_answer()
        game["attempts"] = 10
        await ctx.send(f"🎮 2A1B 遊戲開始！請輸入 !2A1B <4位數字> 來猜。總共有 10 次機會。")
        print(f"[{channel}] 2A1B的答案是 {game['answer']}")
        return

    if not game.get("active", False):
        await ctx.send("⚠️ 目前沒有進行中的遊戲，請重新輸入 `2A1B` 開始新的一場！")
        return

    if game["active"] and channel in two_a_one_b_cooldowns and now - two_a_one_b_cooldowns[channel] < COOLDOWN_TIME:
        remaining = int(COOLDOWN_TIME - (now - two_a_one_b_cooldowns[channel]))
        await ctx.send(f"⏳ 指令冷卻中，請再等 {remaining} 秒！")
        return
    two_a_one_b_cooldowns[channel] = now  # 更新使用時間

    # 嘗試解析玩家輸入
    parts = ctx.message.content.strip().split()
    if len(parts) < 2 or not parts[1].isdigit() or len(parts[1]) != 4:
        await ctx.send(f"{people['name']} 請輸入正確格式： !2A1B <4位數字>")
        return

    guess = parts[1]
    
    # 檢查是否有重複數字
    if len(set(guess)) != 4:
        await ctx.send(f"{people['name']} 請輸入不重複的 4 位數字！")
        return
    
    answer = game["answer"]

    # 計算 A 和 B
    A, B = calculate_ab(answer, guess)
    game["attempts"] -= 1

    if A == 4:
        await ctx.send(f"🎉 {people['name']} 猜對了！答案就是 {answer}！")
        if channel == "justababu":
            await ctx.send(f"!addpoints {people['name']} 200")
        end_game(channel, "2A1B")
        reset_users(channel)
        return

    if game["attempts"] <= 0:
        await ctx.send(f"❌ 遊戲結束！沒有人猜中，答案是 {answer}。")
        end_game(channel, "2A1B")
        reset_users(channel)
        return

    await ctx.send(f"{people['name']} 猜 {guess} → {A}A{B}B，剩餘 {game['attempts']} 次")
    
# 取得玩家資料
def get_user(channel_name, username):
    if channel_name not in users:
        users[channel_name] = {}
    if username not in users[channel_name]:
        users[channel_name][username] = {"name": username, "times": 5}
    return users[channel_name][username]

# 重置某個頻道的玩家資料
def reset_users(channel_name):
    if channel_name in users:
        users[channel_name].clear()
        
# 使用者開關
def game_usercanopen(channel_name, gametype, choice=None):
    if channel_name not in useropen:
        useropen[channel_name] = {}
    # 若 gametype 不存在，預設為 True
    if gametype not in useropen[channel_name]:
        useropen[channel_name][gametype] = True

    # 如果有傳入 Y/N，直接設定 True/False
    if choice is not None:
        if choice.upper() == "Y":
            useropen[channel_name][gametype] = True
        elif choice.upper() == "N":
            useropen[channel_name][gametype] = False
        # choice 非 Y/N 不改變現有值

    else:
        # 沒有傳入選項，維持舊行為：切換狀態
        if useropen[channel_name][gametype]:
            useropen[channel_name][gametype] = False
        else:
            useropen[channel_name][gametype] = True

    return useropen[channel_name][gametype]

# 結束遊戲
def end_game(channel, gametype):
    game = get_game(channel, gametype)
    game["active"] = False
    reset_users(channel)
    if "timeout_task" in game and game["timeout_task"]:
        game["timeout_task"].cancel()
        game["timeout_task"] = None
        
# 取得遊戲狀態
def get_game(channel, gametype):
    if channel not in games:
        games[channel] = {}

    if gametype not in games[channel]:
        if gametype == "ultimate":
            games[channel][gametype] = {
                "active": False,
                "answer": None,
                "low": 0,
                "high": 1000,
                "end": 0,
                "start_time": None,
                "timeout_task": None,
            }
        elif gametype == "2A1B":
            games[channel][gametype] = {
                "active": False,
                "answer": None,
                "attempts": 0,
            }
        else:
            games[channel][gametype] = {"active": False}

    return games[channel][gametype]
#------------------------------------------------遊戲區---------------------------------------------------

        
if __name__ == "__main__":
    global gspread_client # 宣告要修改全域變數
    
    # 步驟 1: 初始化 Gspread 客戶端
    gspread_client = get_gspread_client()
    if gspread_client is None:
        print("警告：Google Sheets 連線失敗，機器人將無法記錄永久次數！")
        
    keep_alive()
    bot.run()
