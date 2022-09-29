from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tkinter import *
from tkinter import messagebox
from tkcalendar import Calendar
from time import sleep
from threading import Thread
from tkHyperlinkManager import *
import webbrowser
from functools import partial


AEROFLOT_URL = 'https://www.aeroflot.ru/sb/app/ru-ru#/search?adults=1&cabin=economy&children=0&infants=0&routes=MOW.2022'

DEST = {
    'Баку': 'BAK',
    'Ереван': 'EVN',
    'Анталья': 'AYT',
    'Бодрум': 'BJV',
    'Стамбул': 'IST',
    'Бишкек': 'FRU',
    'Даламан': 'DLM',
    'Актобе': 'AKX',
    'Алматы': 'ALA',
    'Астана': 'NQZ',
    'Атырау': 'GUW',
    'Караганда': 'KGF',
}


root = Tk()
root['bg'] = '#fafafa'
root.title('Поиск авиабилетов')
root.geometry('500x750')
root.resizable(width=False, height=False)

frame_top = Frame(root, bg='#ffb700', bd=5)
frame_top.place(relx=0, rely=0, relwidth=1, relheight=0.4)

frame_mid = Frame(root, bg='#ffb600', bd=5)
frame_mid.place(relx=0, rely=0.45, relwidth=1, relheight=0.15)

frame_bottom = Frame(root, bg='#FFFFFF', bd=5)
frame_bottom.place(relx=0, rely=0.6, relwidth=1, relheight=0.4)

# dateLabel = Label(frame_top, text='Укажите конец первого временного\n интервала в формате 2021-12-31',
#                   bg='#ffb700', font=('Arial', 12))
# e = Entry(frame_top, justify=LEFT)
# e.insert(END, '2021-09-15')

cal = Calendar(frame_top, selectmode='day')
cal.place(relx=0.3, rely=0)


class DateGetter:
    chosen_date = None

    @staticmethod
    def grad_date():
        rec_date = cal.get_date()
        pos_day = rec_date.find('/')
        day = rec_date[:pos_day]
        if len(day) == 1:
            day = '0' + day
        pos_mth = rec_date[pos_day+1:].find('/')
        month = rec_date[pos_day+1:pos_day+pos_mth+1]
        date.config(text="Selected Date is: " + rec_date)
        DateGetter.chosen_date = day + month


Button(frame_top, text="Выбрать дату", command=DateGetter().grad_date).place(relx=0.3, rely=0.7, relwidth=0.3)
date = Label(frame_top, text="", bg='#ffb700')
date.place(relx=0.3, rely=0.85)

destinations = Label(frame_mid, text="Выбрать направление", bg='#ffb700')
destinations.place(relx=0.4, rely=0)


class DestGetter:
    chosen_dest = []
    buttons = {}

    @classmethod
    def append_dest(cls, dest):
        if cls.buttons[dest][1]:
            cls.chosen_dest.remove(dest)
            cls.buttons[dest][0].config(relief=RAISED)
            cls.buttons[dest][1] = not cls.buttons[dest][1]
        else:
            cls.chosen_dest.append(dest)
            cls.buttons[dest][0].config(relief=SUNKEN)
            cls.buttons[dest][1] = not cls.buttons[dest][1]

    @staticmethod
    def create_buttons():
        relx, rely = 0.05, 0.3
        for name, dest in DEST.items():
            if relx > 0.9:
                relx = 0.05
                rely += 0.4
            DestGetter.buttons[dest] = [Button(frame_mid, text=name, command=lambda i=dest: DestGetter.append_dest(i)), False]
            DestGetter.buttons[dest][0].place(relx=relx, rely=rely, relwidth=0.13)
            relx += 0.15


dg = DestGetter()
dg.create_buttons()


def perform_search():
    if not DestGetter.chosen_dest:
        messagebox.showinfo("Предупреждение", "Добавьте направление.")
    elif not DateGetter.chosen_date:
        messagebox.showinfo("Предупреждение", "Добавьте дату.")
    else:
        dest_to_search = {}
        for key, value in DEST.items():
            if value in DestGetter.chosen_dest:
                dest_to_search[key] = value
        thread = Thread(target=check_aeroflot, args=(dest_to_search, DateGetter.chosen_date))
        thread.start()


def clear_text():
    text.configure(state='normal')
    text.delete(0.0, END)
    text.configure(state='disabled')


Button(frame_bottom, text='Начать поиск', command=perform_search).place(relx=0.35, rely=0, relwidth=0.3)
Button(frame_bottom, text='Очистить', command=clear_text).place(relx=0.75, rely=0, relwidth=0.2)
text = Text(frame_bottom, state='disabled')
text.place(relx=0.05, rely=0.15, relwidth=0.9, relheight=0.8)
scroll = Scrollbar(frame_bottom)
scroll.pack(side=RIGHT, fill=Y)
scroll.config(command=text.yview)
text.config(yscrollcommand=scroll.set)
hyperlink = HyperlinkManager(text)


def compose_url(url, date, dest):
    return url + date + '.' + dest


def check_aeroflot(dests, date):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.headless = True
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    windows_amount = 1
    for i in range(10):
        # print(f'------ПОПЫТКА НОМЕР {i+1}------')
        text.configure(state='normal')
        text.insert(END, f'------ПОПЫТКА НОМЕР {i+1}------\n')
        text.configure(state='disabled')
        for dest, url in dests.items():
            url = compose_url(AEROFLOT_URL, date, url)
            if windows_amount <= len(dests):
                browser.get(url)
            else:
                browser.switch_to.window(browser.window_handles[0])
                windows_amount = 1

            _aeroflot_process(browser, dest, url)
            # print('-----------')
            text.configure(state='normal')
            text.insert(END, '------------\n')
            text.configure(state='disabled')

            browser.execute_script("window.open('');")
            browser.switch_to.window(browser.window_handles[windows_amount])
            windows_amount += 1
        sleep(1)


def _aeroflot_process(browser, dest, url):
    button = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.button")))
    button.click()
    cont = browser.find_element(By.CLASS_NAME, 'frame__container')
    elements = WebDriverWait(browser, 10).until(lambda lmd=cont: lmd.find_elements(By.XPATH, '//div[@role="alert"]')
                                                                 or lmd.find_elements(By.XPATH,
                                                                                      '//div[@class="flight-search"]'))
    if elements[0].get_attribute('class') == 'flight-search':
        # print(f'Что-то нашли в {dest}!')
        # print(f'{len(elements)} вариантов найдено по {url}!')
        text.configure(state='normal')
        text.insert(END, f'Что-то нашли в {dest}!\n')
        text.insert(END, f'{len(elements)} вариантов найдено по ')
        text.insert(END, 'ссылке!\n', hyperlink.add(partial(webbrowser.open, url)))
        for elt in elements:
            time_ = elt.find_element(By.CLASS_NAME, 'flight-search__time-text')
            try:
                price = elt.find_element(By.CLASS_NAME, 'flight-search__price-text')
            except:
                price = elt.find_element(By.XPATH, '//div[@class="h-display--inline h-text--nowrap"]')
            # print(price.text[:-1] + 'рублей за ' + time_.text)
            text.insert(END, price.text[:-1] + 'рублей за ' + time_.text + '\n')
        text.configure(state='disabled')
    else:
        # print(elements[0].text)
        text.configure(state='normal')
        text.insert(END, elements[0].text + '\n')
        text.configure(state='disabled')


if __name__ == '__main__':
    root.mainloop()
    # check_aeroflot(('https://www.aeroflot.ru/sb/app/ru-ru#/search?adults=1&cabin=economy&children=0&infants=0&routes=MOW.20220927.BAK&_k=zmysi9',))
    # check_aeroflot(('https://www.aeroflot.ru/sb/app/ru-ru#/search?adults=1&cabin=economy&children=0&infants=0&routes=MOW.20221013.BAK&_k=d0ryb8',))
    # check_aeroflot(('https://www.aeroflot.ru/sb/app/ru-ru#/search?adults=1&cabin=economy&children=0&infants=0&routes=MOW.20221003.DLM&_k=vnafje',))
    # check_aeroflot(DEST)


