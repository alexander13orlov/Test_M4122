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

def log(message):
    logging.info(message)

def send_and_expect(ser, send_bytes, expected_bytes, timeout, description):
    ser.timeout = timeout
    ser.write(send_bytes)
    log(f"Отправлено ({description}): {send_bytes.hex().upper()}")
    start_time = time.perf_counter()
    response = ser.read(len(expected_bytes))
    elapsed = time.perf_counter() - start_time

    if response == expected_bytes:
        log(f"Получен ожидаемый ответ ({description}): {response.hex().upper()} через {elapsed:.3f} сек.")
        return True
    else:
        log(f"Ответ не получен или неверный ({description}). Получено: {response.hex().upper()} через {elapsed:.3f} сек.")
        return False

def send_and_expect_single(ser, send_byte, expected_byte, timeout, description):
    return send_and_expect(ser, send_byte, expected_byte, timeout, description)

def wait_for_range_response(ser, start_byte, end_byte, max_length=11, timeout=5):
    ser.timeout = timeout
    buffer = bytearray()
    start_time = time.perf_counter()

    while True:
        byte = ser.read(1)
        if not byte:
            break
        buffer.append(byte[0])

        if buffer[0] != start_byte:
            buffer.clear()
            continue

        if buffer[-1] == end_byte and len(buffer) >= 2:
            elapsed = time.perf_counter() - start_time
            log(f"Получен полный ответ ({len(buffer)} байт) за {elapsed:.3f} сек: {buffer.hex().upper()}")
            return buffer

        if len(buffer) >= max_length:
            break

    elapsed = time.perf_counter() - start_time
    log(f"Ответ не получен полностью за {elapsed:.3f} сек. Получено: {buffer.hex().upper()}")
    return None

def listen_for_additional_data(ser, duration_sec=15):
    log(f"Начинаем прослушку порта на {duration_sec} секунд...")
    ser.timeout = 0.5
    start_time = time.perf_counter()
    while (time.perf_counter() - start_time) < duration_sec:
        byte = ser.read(1)
        if byte:
            elapsed = time.perf_counter() - start_time
            log(f"Получен дополнительный байт через {elapsed:.3f} сек: {byte.hex().upper()}")

def main():
    port_name = 'COM2'  # Указать свой порт
    baudrate = 9600

    try:
        log(f"Открытие порта {port_name}...")
        ser = serial.Serial(port=port_name, baudrate=baudrate, bytesize=8, parity='N', stopbits=1, timeout=2)
        time.sleep(2)
        log("Порт успешно открыт.")

        for i in range(1, 4):
            log(f"[{i}/3] Проверка связи (0x55 <-> 0x55)")
            send_and_expect_single(ser, b'\x55', b'\x55', 2, "Проверка связи")

        log("Отправка команды настройки.")
        config_and_start = bytes.fromhex('6B64006D01')
                
        log("Повторная проверка связи (0x55 <-> 0x55)")
        send_and_expect_single(ser, b'\x55', b'\x55', 2, "Повторная проверка связи")
        log("Пауза для записи флеш")
        time.sleep(2)
        
        config_and_start = bytes.fromhex('58')
        log("Отправка команды настройки и запуска измерения.")
        ser.write(config_and_start)
       
        log("Ожидание 0x5B окончания измерения. (ответ на запуск измерения 0x58)...")
        ser.timeout = 15
        start_time = time.perf_counter()
        resp = ser.read(1)
        elapsed = time.perf_counter() - start_time
        if resp == b'\x5B':
            log(f"Ответ 0x5B получен через {elapsed:.3f} сек.")
        else:
            log(f"Ответ 0x5B не получен. Завершено через {elapsed:.3f} сек.")
            return

        # log("Повторная проверка связи (0x55 <-> 0x55)")
        # send_and_expect_single(ser, b'\x55', b'\x55', 2, "Повторная проверка связи")
        log("Пауза. Если после нее омметр запустит измерение, то это несанкционированный запуск")
        # time.sleep(5)
        log("Отправка команды запроса результатов: 0x5C")
        ser.write(b'\x5C')

        log("Ожидание ответа от 0x5D до 0x5E...")
        result = wait_for_range_response(ser, start_byte=0x5D, end_byte=0x5E, max_length=11, timeout=5)
        if result is None:
            log("Результат не получен или неполный.")

        # слушаем порт ещё 11 секунд
        listen_for_additional_data(ser, duration_sec=10)

    except serial.SerialException as e:
        log(f"Ошибка COM-порта: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            log("Порт закрыт.")

if __name__ == '__main__':
    main()
