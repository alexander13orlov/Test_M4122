import serial
import time
import logging
from datetime import datetime

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log(msg):
    logging.info(msg)

def main():
    port_name = 'COM3'  # Измените на нужный порт
    baudrate = 9600
    timeout = 2

    try:
        log(f"Открытие порта {port_name}...")
        ser = serial.Serial(port=port_name, baudrate=baudrate, bytesize=8, parity='N', stopbits=1, timeout=timeout)
        time.sleep(2)  # Небольшая задержка после открытия порта
        log("Порт открыт.")

        # Шаги 2-3: Проверка связи (отправка 0x55 и ожидание ответа 0x55 три раза)
        for attempt in range(1, 4):
            log(f"[{attempt}/3] Отправка байта проверки связи: 0x55")
            ser.write(b'\x55')
            start_time = time.perf_counter()
            response = ser.read(1)
            elapsed = time.perf_counter() - start_time

            if response == b'\x55':
                log(f"Ответ 0x55 получен через {elapsed:.3f} сек.")
            else:
                log(f"Нет ответа или ответ неверный. Ожидание завершилось через {elapsed:.3f} сек.")

        # Шаг 4: Отправка команды настройки
        setup_command = bytes.fromhex('6B64006D01')
        log(f"Отправка команды настройки прибора: {setup_command.hex().upper()}")
        ser.write(setup_command)

        # Шаг 4.1: Отправка команды запуска измерения
        log("Отправка команды запуска измерения: 0x58")
        ser.write(b'\x58')

        # Шаг 5: Ожидание ответа 0x5B в течение 15 сек
        ser.timeout = 15
        start_time = time.perf_counter()
        response = ser.read(1)
        elapsed = time.perf_counter() - start_time

        if response == b'\x5B':
            log(f"Ответ 0x5B получен через {elapsed:.3f} сек.")
        else:
            log(f"Ожидание ответа 0x5B завершилось через {elapsed:.3f} сек. Ответ не получен.")

    except serial.SerialException as e:
        log(f"Ошибка работы с COM портом: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            log("Порт закрыт.")

if __name__ == '__main__':
    main()
