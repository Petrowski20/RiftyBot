import logging
import os
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from googleapiclient.discovery import build # type: ignore
from google.oauth2.service_account import Credentials # type: ignore

# Configura tu token de Telegram
TELEGRAM_API_TOKEN = '7695366938:AAFdpSLDXMom1fgXg3UGWnuX-h4w958MpXI'

# Configura las credenciales para Google Sheets
SHEET_ID = '1meJnfziPVE_WeS4fXA_Af434ttWmCI7uCWhjFIRv7Kc'  # El ID de tu hoja de Google Sheets
RANGE_NAME = 'CalendarioLEC25!A2:G100'  # El rango de la hoja donde están los partidos

# Configura las credenciales de Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SERVICE_ACCOUNT_FILE = "credentials.json"

# Definir los equipos
EQUIPOS = {
    'G2': 'G2 Esports',
    'FNC': 'Fnatic',
    'MKOI': 'Movistar KOI',
    'SK': 'SK Gaming',
    'RGE': 'Rogue',
    'TH': 'Team Heretics',
    'BDS': 'Team BDS',
    'VIT': 'Team Vitality',
    'GX': 'GiantX',
    'KC': 'Karmine Corp'
}

# Configurar logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Función para leer los partidos del calendario
def get_calendar():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    # Leer los datos de la hoja
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    today = datetime.date.today()
    todays_games = []

    for row in values:
        date = row[0]
        if date == str(today):  # Compara con la fecha de hoy
            comp = row[1]  # Competición (Columna B)
            formato = row[2]  # Formato (Columna C)
            if comp.strip() == "INVIERNO LEC 25":
                games = row[3:]  # Los partidos están en las columnas D en adelante
                games = [game.strip() for game in games if game]  # Filtrar las celdas vacías
                if formato in ["Bo3", "Bo5"]:
                    games = [generate_bo3_or_bo5_options(game, formato) for game in games]
                todays_games = [game for sublist in games for game in sublist]  # Aplanar la lista
                break

    return todays_games

def generate_bo3_or_bo5_options(partido, formato):
    equipo1, equipo2 = partido.split(" vs ")
    if formato == "Bo3":
        return [
            f"{equipo1} 2-0 {equipo2}",
            f"{equipo1} 2-1 {equipo2}",
            f"{equipo1} 1-2 {equipo2}",
            f"{equipo1} 0-2 {equipo2}"
        ]
    elif formato == "Bo5":
        return [
            f"{equipo1} 3-0 {equipo2}",
            f"{equipo1} 3-1 {equipo2}",
            f"{equipo1} 3-2 {equipo2}",
            f"{equipo1} 2-3 {equipo2}",
            f"{equipo1} 1-3 {equipo2}",
            f"{equipo1} 0-3 {equipo2}"
        ]
    return []

# Comando /calendario para obtener los partidos de hoy
async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Obtener los partidos de hoy
    partidos = get_calendar()

    if partidos:
        mensaje = "\n".join(partidos)
        await update.message.reply_text(mensaje)
    else:
        await update.message.reply_text("No hay partidos programados para hoy.")

def main():
    # Sustituye 'TELEGRAM_API_TOKEN' por tu token real
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()
    
    # Comando para obtener el calendario
    application.add_handler(CommandHandler("calendario", calendario))
    
    # Ejecuta el bot
    application.run_polling()

if __name__ == '__main__':
    main()