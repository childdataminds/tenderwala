class Urdu:
    def __init__(self):
        self.user = "معزز صارف"
        self.sender = ""
        self.type = "ur"
      
        
        self.province = [
"پنجاب کے شہروں",
"سندھ کے شہروں",
"خیبر پختونخوا کے شہروں",
"آزاد کشمیر کے شہروں",
"بلوچستان کے شہروں",
"گلگت بلتستان کے شہروں"
]
    def all_tenders_already_sent(self,prov):
        return f"""
آپ کی ترجیحات کے مطابق مزید ٹینڈر موجود نہیں ہیں۔
جیسے ہی اپلوڈ ہونگے آپ مجھ سے طلب کر سکتے ہیں

*{prov}*
"""
    def no_tender_available_msg(self,prov):
        return f"""
اس وقت میرے پاس مندرجہ ذیل صوبوں اور ریجن کے ٹینڈر موجود نہیں ہیں:

{prov}
"""
    def choose_from_img(self,service):
      return f"""
        اپنی ترجیحات کے مطابق *{service}* کا انتخاب کریں
        
        *مجھے نمبر بھیجیں *مثلاَ 1,3,5
        
        اگر سب کو شامل کرنا ہے تو مجھے *ALL* لکھ کر بھیجیں۔
        """
    def tender_msg(self,col,data):
        msg = f"""

            ❇️❇️🚨Tender of {col}🚨❇️❇️
            Title: *{data[0]}*

            Publish Date📊: *{data[1]}*
            Opening Date✅: *{data[2]}*

            Department🏢: *{data[3]}*
            City🏠:*{data[4]}*

            Note: _{data[5]}_

            Good Luck!
                """
        return str(msg)
       
    def messages(self):
        self.paid_user_1 = f"""
                        کیسے ہیں آپ؟ اُپ پہلے سے ہی ہماری ٹینڈر سروس میں شامل ہیں اور ہم آپ کو روزانہ کی بنیاد پر معلومات فراہم کرتے رہیں گے۔ ہمارے ساتھ کام پروگرام میں شامل ہونے کا شکریہ۔ کمپنی کی جانب سے میں 
                        ہمیشہ آپ کی خدمت میں حاضر ہوں
                        
                        
                        Hey, {self.user}, you are already registered to our tenders service. We are pleased that you have joined our platform. We'll be always sending you latest
                        tenders update of your selected categories. Thank you for bearing with us.
                        """
        self.paid_user_2 = f"""
                        {self.user} آپ ہمارے پروگرام میں رجسٹر ہیں  اور آپ کو میں  روزانہ صبح 9 بجے تازہ ترین ٹینڈر فراہم کرتا رہوں گا۔ 
👈🏻 اپنی سبسکرپشن کی معلومات کے لیے  مجھے "info/" کی کمانڈ دیں
👈🏻 پلان میں تبدیلی یا شعباجات میں ردو بدل کے لیے مجھے "settings/" کی کمانڈ دیں۔
                        """
        self.is_user_1 = f"""
                        خوش آمدید {self.user} 😎,
        آپ ہمارے پلیٹ فارم پر رجسٹر ہیں 🤩 میں  آپ کی طرف سے فیس جمع ہونے کا انتظار کر رہا ہوں 🥹 ۔
 اہم نوٹ ✍️: 
😧 فیس کی ادائیگی کے بعد مجھے سرین شاٹ سینڈ کریں اور مجھے "complete/" کی کمانڈ دیں ۔ اس کے بعد میں اکائنٹس دپارٹمنٹ سے تصدیق کے بعد آپ کی سروس فعال کر دوں گاْ اور روزانہ کی بنیاد پر آپ کو معلومات فراہم کروں گا۔
                        """
        self.is_user_2 = f"""
                        {self.user},
         آپ کی رجسٹریشن مکمل ہو چکی ہے لیکن فیس کی ادائگی تک میں آپ کو معلومات فراہم نہیں کر سکتا 😑!

🫸🏻فیس کی ادائیگی کے بعد مجھے سرین شاٹ سینڈ کریں اور مجھے "complete/" کی کمانڈ دیں ۔ اس کے بعد میں اکائنٹس دپارٹمنٹ سے تصدیق کے بعد آپ کی سروس فعال کر دوں گاْ اور روزانہ کی بنیاد پر آپ کو معلومات فراہم کروں گا۔
                        """
        self.new_user_1 = f"""
                        السلام علیکم {self.user} !
    👈🏻 میں ہوں آپ کا ٹینڈر والا۔
     میں AI سے بناایک روبوٹ 🤖 ہوں ۔ میں آپ کے کاروبار کے لیے روزانہ کی بنیاد پرٹینڈرز کی مکمل معلومات جمع کرتا ہوں تاکہ آپ کو بروقت اور تازہ ترین معلومات فراہم کر سکوں۔
    👈🏻 ابھی ہماری سروس میں شامل ہوں اور روزانہ صبح 9 بجے تمام نئے ٹینڈر خواہ وہ کسی بھی ادارے میں شائع ہوے ہوں ، میں انہیں آپ کے لیے آپ کے  واٹسپ پر مہیا کروں گا۔
    👈🏻 سب سے بہترین 🫶 چیز یہ ہے کہ میں آپ کو آپ کی کاروباری ضرورت کے مطابق مخصوص شہروں اور مخصوص شعبوں کے ٹینڈر دینے کی صلاحیت رکھتا ہوں۔ بس آپ کو کرنا یہ ہے کہ رجسٹر ہوتے وقت شعبے اورcategory کا انتخاب دھیان سے کریں!
                        
    
                        """
        self.new_user_2 = f"""
                    {self.user}🙄!
                    آپ ابھی تک رجسٹر نہیں ہیں اور پماری سروسز حاصل کرنے کے لیے رجسٹر ہونا ضروری ہے! 
                    """
        self.contact_us = """
                    میرے متعلق معلومات اور شکایات کے لیے کمپنی کے نمائندے سے واٹسیپ پر رابطہ کریں
                    \n\n
                    0305 6842507
                    """
        self.register_msg = """
        
        """
        self.extra_help = """
                    اگر آپ فری ڈیمو لینا چاہتے ہیں یا رجسٹریشن میں کوئی مدد لینا چاہتے ہیں تو درج ذیل نمبر پر نمائندے سے رابطہ کریں
                    \n
                    Whatsapp 0305 6842507
        """
        self.ask_prov = """
        *Step-1*
        
       آپ کن *صوبوں* کے *ٹینڈر* موصول کرنا چاہتے ہیں؟

1️⃣ پنجاب
2️⃣ سندھ
3️⃣ بلوچستان
4️⃣ خیبر پختونخوا
5️⃣آزاد کشمیر
6️⃣ گلگت بلتستان
7️⃣ وفاق

آپ جن صوبوں کے ٹینڈر حاصل کرنا چاہتے ہیں ان سب کے نمبر مجھے لکھ کر بھیج دیں۔

مثلا  1,2,5
        
       👇 اور اگر آپ تمام صوبوں کا انتخاب کرنا چاہتے ہیں تو نیچے دیے گئے آل کا بٹن دبایئں 
        """
        self.province_success = """
          ✅آپ کے منتخب کردہ *ترجیحات* محفوظ کر لی گئے ہیں۔
        """
        self.province_error = """
        درج ذیل درست نہیں ہے: \n
        """
        self.ask_types = """
                *Step-2*
        
       آپ کن *اقسام* کے *ٹینڈر* موصول کرنا چاہتے ہیں؟

1️⃣ Goods
2️⃣ Works
3️⃣ Services

آپ جن اقسام کے ٹینڈر حاصل کرنا چاہتے ہیں ان سب کے نمبر مجھے لکھ کر بھیج دیں۔

مثلا 1,2
        
       👇 اور اگر آپ تمام اقسام کا انتخاب کرنا چاہتے ہیں تو نیچے دیے گئے آل کا بٹن دبایئں 
        """
        
        self.register_success = """
        ٹینڈر والا میں خوش آمدید
        
        اُ کا فری ٹرائل ایک مہینے کے لیے شروع کر دیا گیا ہے۔
        """
        self.keep_registering = """
        آپ فری ڈیمو ❇️کے لیے اکاؤنٹ سیٹ اپ کر رہے ہیں۔ دی گئی ہدایات کے مطابق اکاؤنٹ کا پراسس مکمل کر لیں اس کے بعد ہی میری سروس استعمال کی جا سکتی ہے۔🥴
        """
        
class English:
    def __init__(self):
          self.user = "Dear Customer"
          self.sender = ""
          self.type = "en"
    
          self.province = [
'Cities of Punjab',
'Cities of Sindh',
'Cities of KPK',
'Cities of AJK',
'Cities of Balochistan',
'Cities of Gilgit'
]
    def all_tenders_already_sent(self,prov):
        return f"""
There are *NO MORE* latest tenders are available for:
{prov}
I have already sent you all available tenders. 
"""
    def no_tender_available_msg(self,prov):
        return f"""
*No Tenders* available for:

{prov}

I will collect latest tenders shortly and will send it to you on your next request.
"""
    def choose_from_img(self,service):
        return f"""
        Choose your desired *{service}* from above 👆 image and reply me with *serial number*
        
        (for example 1,3,5)
        
        If you want to choose all, reply me with *ALL*
        """
    def tender_msg(self,col,data):
        msg = f"""

❇️❇️🚨Tender of {col}🚨❇️❇️
Title: *{data[0]}*

Publish Date📊: *{data[1]}*
Opening Date✅: *{data[2]}*

Department🏢: *{data[3]}*
City🏠:*{data[4]}*

Note: _{data[5]}_

Good Luck!
    """
        return str(msg)
       
    def messages(self):
          # TenderWala User Messages (English Version)

        self.paid_user_1 = f"""
        How are you? You are already part of our Tender Service, and we will continue to provide you with information on a daily basis. 
        Thank you for joining our program. On behalf of the company, I am always at your service.

        Hey, {self.user}, you are already registered to our tender service. 
        We are pleased that you have joined our platform. 
        We will always send you the latest tender updates from your selected categories.
        Thank you for staying with us.
        """

        self.paid_user_2 = f"""
        {self.user}, you are registered in our program and I will provide you with the latest tenders every day at 9 AM.

        👈🏻 To check your subscription details, send the command: "info/"
        👈🏻 To change your plan or modify your selected categories, send the command: "settings/"
        """

        self.is_user_1 = f"""
        Welcome {self.user} 😎,

        You are registered on our platform 🤩. I am currently waiting for your fee payment 🥹.

        Important Note ✍️:
        After making the payment, please send me a screenshot and type the command "complete/". 
        After confirmation from the Accounts Department, I will activate your service and start providing daily updates.
        """

        self.is_user_2 = f"""
        {self.user},

        Your registration has been completed, but I cannot provide you with information until the fee is paid 😑!

        After making the payment, please send me a screenshot and type the command "complete/". 
        After confirmation from the Accounts Department, I will activate your service and provide you with daily updates.
        """

        self.new_user_1 = f"""
        *Assalamualaikum* {self.user}!

        👈🏻 I am your *TenderWala*.
        I am an *AI-based bot* 🤖. I collect complete *tender* information daily for your business so that I can provide you with timely and up-to-date updates.

        👈🏻 Join our service now, and every day at *9 AM* I will deliver all newly published tenders — *from any department* — directly to your *WhatsApp*.

        👈🏻 The best 🫶 part is that I can provide tenders according to your *business needs*, specific *province*, and specific *sectors*. 
        Just carefully select your sectors and categories!

        
        """

        self.new_user_2 = f"""
        {self.user} 🙄!

        You are *not registered* yet, and registration is required to access our services!
        """
        self.contact_us = """
        Here is the *Whatsapp Number* of our company representative for any queries or complaints about me🫢:
        \n\n
        0305 6842507
        """
        self.register_mgs = """
        
        """
        self.extra_help = """
                If you want to get FREE Demo or you want to get help in registration process, you can contact to our representative
                \n 
                Whatsapp 0305 6842507
        """
        self.ask_prov = """
        *Step-1*
        
        Choose the *provices/sectors* you want to receive the tenders from:
        
1️⃣ Punjab
2️⃣ Sindh
3️⃣ Blochistan
4️⃣ KPK
5️⃣ AJK
6️⃣ Gilgit-Bultistan
7️⃣ Federal
        
        Reply with *serial-numbers* of your choises
        
        *For Example*: 1,4,7
        It means you are choosing *Punjab*, *KPK* & *Federal*
        
        Or if you want to choose all, press All button below 👇 
        """
        self.province_success = """
        Your *selected choices* have been saved succefully ✅
        """
        self.province_error = """
        This value is not correct: 
        """
        self.ask_types = """
        *Step-2*
        
        Choose the *contract type* you want to receive the tenders from:
        
1️⃣ Goods
2️⃣ Works
3️⃣ Services

        
        Reply with *serial-numbers* of your choises
        
        *For Example*: 1,3
        It means you are choosing *Goods* & *Services*
        
        Or if you want to choose all, press All button below 👇 
        """
        self.keep_registering = """
        You need to complete your *account setup* before you can start your *Free Trial*🎓 of *1-Month*. 
        You can change your *settings*🔧 anytime.
        """
        self.register_success = """
        Welcome to *TenderWala*
        
        Your *Free Trial for 1-Month* has been *Initiated*
        
        You can now *enjoy* latest *tenders updates* anytime. 
        """
