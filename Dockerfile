FROM python:3.9

# Установка локалей и кодировки
RUN apt-get update && apt-get install -y locales locales-all && rm -rf /var/lib/apt/lists/* \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8

# Установка временной зоны в Московское время
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# Установить рабочую директорию
WORKDIR /RPI_Bot

# Скопируйте и установите зависимости
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Скопируйте ваше приложение в контейнер
COPY . .
RUN chmod 777 token_3.json

# Определить порт, который будет слущать ваше приложение
EXPOSE 3000