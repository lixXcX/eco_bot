import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image
from ultralytics import YOLO
import os

logging.basicConfig(
    format='%(asitime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    model = YOLO('yolo11n.pt')
    logger.info("Модель YOLO успешно загружена!")
except Exception as e:
    logger.error(f"Ошибка загрузки модели YOLO: {e}")
    model = None

eco_knowledge = {
    "bottle": {
        "name": "🥤 Пластиковая бутылка",
        "bin": "🚮 Контейнер: Желтый или отдельный для пластика",
        "prepare": "🧼 Подготовка: Снять крышку, смять бутылку, сполоснуть",
        "fact": "💡 Факт: Пластиковая бутылка разлагается 450-1000 лет!"
    },
    "plastic bottle": {
        "name": "🥤 Пластиковая бутылка",
        "bin": "🚮 Контейнер: Желтый или отдельный для пластика",
        "prepare": "🧼 Подготовка: Снять крышку, смять бутылку, сполоснуть",
        "fact": "💡 Факт: Пластиковая бутылка разлагается 450-1000 лет!"
    },
    "wine glass": {
        "name": "🥃 Стеклянная тара",
        "bin": "🍾 Контейнер: Зеленый или отдельный для стекла",
        "prepare": "🧼 Подготовка: Ополоснуть, снять крышку/пробку",
        "fact": "💡 Факт: Стекло можно перерабатывать бесконечно без потери качества. Разлагается 1000+ лет!"
    },
    "glass": {
        "name": "🥃 Стеклянная тара",
        "bin": "🍾 Контейнер: Зеленый или отдельный для стекла",
        "prepare": "🧼 Подготовка: Ополоснуть, снять крышку/пробку",
        "fact": "💡 Факт: Стекло можно перерабатывать бесконечно без потери качества. Разлагается 1000+ лет!"
    },
    
    "book": {
        "name": "📦 Бумага/Картон",
        "bin": "📋 Контейнер: Синий или отдельный для бумаги",
        "prepare": "📄 Подготовка: Убрать скрепки, скотч, пластиковые элементы",
        "fact": "💡 Факт: Переработка одной тонны бумаги спасает 17 деревьев!"
    },
    "cardboard": {
        "name": "📦 Бумага/Картон",
        "bin": "📋 Контейнер: Синий или отдельный для бумаги",
        "prepare": "📄 Подготовка: Сложить, убрать скотч и пластик",
        "fact": "💡 Факт: Переработка картона экономит 70% энергии по сравнению с производством нового!"
    },
    
    "can": {
        "name": "🥫 Алюминиевая банка",
        "bin": "🥫 Контейнер: Желтый или отдельный для металла",
        "prepare": "🧼 Подготовка: Сполоснуть, смять",
        "fact": "💡 Факт: Алюминиевая банка может быть переработана и снова оказаться на полке через 60 дней!"
    },
    
    "battery": {
        "name": "🔋 Батарейка",
        "bin": "⚠️ Контейнер: Специальный пункт приема (НЕ ВЫБРАСЫВАТЬ В ОБЫЧНЫЙ МУСОР!)",
        "prepare": "🔋 Подготовка: Заклеить контакты скотчем, сдать в пункт приема",
        "fact": "💡 Факт: Одна пальчиковая батарейка отравляет 20 кв. метров земли или 400 литров воды!"
    },
    
    "apple": {
        "name": "🍎 Пищевые отходы",
        "bin": "🌱 Контейнер: Для органики (обычно коричневый) или компост",
        "prepare": "🍂 Подготовка: Можно использовать для компоста",
        "fact": "💡 Факт: На свалке пищевые отходы выделяют метан (парниковый газ), а в компосте становятся удобрением!"
    },
    "banana": {
        "name": "🍌 Пищевые отходы",
        "bin": "🌱 Контейнер: Для органики (обычно коричневый) или компост",
        "prepare": "🍂 Подготовка: Можно использовать для компоста",
        "fact": "💡 Факт: На свалке пищевые отходы выделяют метан (парниковый газ), а в компосте становятся удобрением!"
    },
    
    "cup": {
        "name": "☕ Одноразовый стаканчик",
        "bin": "⚠️ Сложный случай! Обычно не перерабатывается из-за пластикового покрытия",
        "prepare": "🚮 Подготовка: Если есть значок переработки - в пластик, иначе в общий мусор",
        "fact": "💡 Факт: Бумажные стаканчики покрыты пластиком, поэтому их сложно перерабатывать. Лучше использовать многоразовую кружку!"
    },
    "plastic bag": {
        "name": "🛍️ Пакет пластиковый",
        "bin": "🔄 Контейнер: Для мягкого пластика (обычно отдельные боксы в магазинах)",
        "prepare": "🧼 Подготовка: Очистить, сложить компактно",
        "fact": "💡 Факт: Пакет используется в среднем 20 минут, а разлагается 200 лет!"
    }
}

main_keyboard = [
    [KeyboardButton("🥤 Пластик")],
    [KeyboardButton("🥃 Стекло")],
    [KeyboardButton("📦 Бумага/Картон")],
    [KeyboardButton("🥫 Металл")],
    [KeyboardButton("🔋 Батарейки")],
    [KeyboardButton("🍎 Органика")],
    [KeyboardButton("❓ Другое (спросить по фото)")]
]

button_info = {
    "🥤 Пластик": eco_knowledge["bottle"],
    "🥃 Стекло": eco_knowledge["glass"],
    "📦 Бумага/Картон": eco_knowledge["book"],
    "🥫 Металл": eco_knowledge["can"],
    "🔋 Батарейки": eco_knowledge["battery"],
    "🍎 Органика": eco_knowledge["apple"],
    "❓ Другое (спросить по фото)": None
}

def format_eco_info(item_key):
    if item_key not in eco_knowledge:
        return None
    
    info = eco_knowledge[item_key]
    return f"""
{info['name']}

{info['bin']}
{info['prepare']}
{info['fact']}
    """

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    reply_markup = ReplyKeyboardMarkup(
        main_keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    welcome_text = f"""
🌍 Здравствуйте, {user.first_name}! Я помогу вам разобраться, как правильно отсортировывать мусор.

Что я умею:
📸 Отправьте фото отхода - я определю его тип
👆 Или выберите категорию из меню ниже
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text in button_info:
        if text == "❓ Другое (спросить по фото)":
            await update.message.reply_text("📸 Отправьте фото предмета, и я постараюсь определить его тип и рассказать, как утилизировать!")
        else:
            info = button_info[text]
            if info:
                response = f"""
{info['name']}

{info['bin']}
{info['prepare']}
{info['fact']}
                """
                await update.message.reply_text(response)
    else:
        await update.message.reply_text("Пожалуйста, выберите категорию из меню или отправьте фото.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if model is None:
        await update.message.reply_text("😵 Ошибка: модель распознавания не загружена.")
        return

    await update.message.reply_text("🔍 Анализирую фото... Это займет несколько секунд.")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = BytesIO()
        await photo_file.download_to_memory(photo_bytes)
        photo_bytes.seek(0)
        
        img = Image.open(photo_bytes)
        
        results = model(img)
        
        eco_items_found = []
        if results and len(results) > 0:
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                class_name = results[0].names[class_id].lower()
                
                if class_name in eco_knowledge:
                    eco_items_found.append(class_name)
                else:
                    for eco_key in eco_knowledge:
                        if class_name in eco_key or eco_key in class_name:
                            eco_items_found.append(eco_key)
                            break
        
        eco_items_found = list(set(eco_items_found))
        
        if eco_items_found:
            response = "🌱 На фото найдено:\n\n"
            for item in eco_items_found:
                response += format_eco_info(item) + "\n" + "-"*30 + "\n"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                "🤔 На фото не найдены предметы для переработки.\n\n"
                "Возможно, это:\n"
                "• Предмет, который я пока не умею распознавать\n"
                "• Не мусор (попробуйте другой ракурс)\n\n"
                "Выберите категорию из меню или отправьте другое фото!"
            )
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("😔 Ошибка при обработке. Попробуйте еще раз или воспользуйтесь кнопками.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я понимаю только команды из меню или фотографии!\n"
        "Нажмите /start, чтобы увидеть меню."
    )

def main():
    my_token = "//////"
    
    application = Application.builder().token(my_token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(🥤 Пластик|🥃 Стекло|📦 Бумага/Картон|🥫 Металл|🔋 Батарейки|🍎 Органика|❓ Другое \(спросить по фото\))$'), handle_buttons))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🌍 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 


