import asyncio
import logging
from telegram.ext import Application
import datetime
import pytz
import os

logging.basicConfig(level=logging.INFO)

async def test_job(context):
    print(f"[{datetime.datetime.now()}] Job executed successfully!")

async def main():
    # Создаем фейковое приложение без токена
    app = Application.builder().token("12345:ABC-DEF1234ghIkl-zyx5cM2").build()
    
    # Настраиваем job на через 3 секунды
    t = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(seconds=3)
    t_time = datetime.time(hour=t.hour, minute=t.minute, second=t.second, tzinfo=t.tzinfo)
    
    print(f"Scheduling job at {t_time}")
    app.job_queue.run_daily(test_job, time=t_time)
    
    await app.initialize()
    await app.start()
    
    print("Waiting for job to execute...")
    await asyncio.sleep(5)
    
    await app.stop()
    await app.shutdown()
    print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
