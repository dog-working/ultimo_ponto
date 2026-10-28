import csv
import datetime
import locale
import logging
import os
import random
import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import WebDriverException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import schedule

#QUANTIDADE DE PONTOS 2 OU 4
__QTD_PONTOS__   = 4

#HORARIO ENTRADA/SAIDA 1
__HH_ENTRADA_1__ = 8
__HH_SAIDA_1__   = 12

#HORARIO ENTRADA/SAIDA 2
__HH_ENTRADA_2__ = 13
__HH_SAIDA_2__   = 18

#VARIAÇÃO MÁXIMA DE MINUTOS PARA ENTRADA E SAIDA
__VAR_MM__       = 15

__FIRST_TIME__     = True
__DIAS_DA_SEMANA__ = [0, 1, 2, 3, 4]

__HORARIO__        = '00:00'
__HORARIO_AUX__    = '00:00'
__N_DAILY_REG__    = 0
__MAX_ADD__        = 0
__ARGS_1__         = ''
__ARGS_2__         = ''
__MES_ATUAL__      = 0
__FERIADOS__       = []


__LOGGER__ = logging.getLogger(__name__)
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')


def arma_rotina(tipo_horario: int) -> None:

    global __FIRST_TIME__
    
    if not __FIRST_TIME__:

        schedule.clear()

    if check_weekday():

        match tipo_horario:

            case 1:

                adiciona_horario()
                schedule.every().day.at(__HORARIO__).do(pre_justificativa)

            case _:

                check_horario()
                schedule.every().day.at(__HORARIO__).do(pre_registro)  


def getset_args() -> None:

    global __ARGS_1__
    global __ARGS_2__
    global __MES_ATUAL__

    with open('keys.csv', mode='r', encoding='utf-8') as file:
    
            leitor = csv.reader(file, delimiter=',')
    
            __ARGS_1__, __ARGS_2__ = next(leitor)

    if os.path.exists('keys.csv'):

        os.remove('keys.csv')

    __MES_ATUAL__ = datetime.datetime.now().month


def pre_registro() -> None:

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Firefox(options)

    try:

        registro_ponto(driver)
        arma_rotina(tipo_horario=0)

    except WebDriverException as e:

        arma_rotina(tipo_horario=1)

    finally:

        driver.quit()   
            

def pre_justificativa() -> None:

    global __MAX_ADD__

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Firefox(options)

    try:

        justificativa_ponto(driver)
        arma_rotina(tipo_horario=0)

    except WebDriverException as e:

        if __MAX_ADD__ <= 4:

            __MAX_ADD__ += 1
            arma_rotina(tipo_horario=1)

        else:

            __MAX_ADD__ = 0
            arma_rotina(tipo_horario=0)

    finally:

        driver.quit()


def check_weekday() -> None:

    global __DIAS_DA_SEMANA__
    global __N_DAILY_REG__
    global __MES_ATUAL__
    
    agora = datetime.datetime.now()

    if __MES_ATUAL__ != agora.month:

        __MES_ATUAL__ = agora.month
        get_feriados()

    if agora.weekday() in __DIAS_DA_SEMANA__ and agora.day not in __FERIADOS__ and __N_DAILY_REG__ < __QTD_PONTOS__:

        return True
    
    elif agora.weekday() + 1 in __DIAS_DA_SEMANA__ and agora.day + 1 not in __FERIADOS__:

        return True

    else:

        while agora.weekday() not in __DIAS_DA_SEMANA__ or agora.day in __FERIADOS__:

            time.sleep(3600)
            agora = datetime.datetime.now()
        
        return True


#E QUANDO NÃO TIVER NENHUM FERIADO? O QUE ACONTECE?
def get_feriados() -> None:
    
    with open('feriados.csv', mode='r', encoding='utf-8') as file:

        leitor = csv.reader(file, delimiter=',')

        for x, linha in enumerate(leitor):
            if int(linha[0]) == __MES_ATUAL__: 
                for i in linha[1:]:
                    __FERIADOS__.append(int(i))


def write_log() -> None:

    global __LOGGER__

    agora = datetime.datetime.now()
    logging.basicConfig(filename='.logs_main', level=logging.INFO)
    __LOGGER__.info(f'{agora.strftime('%d/%m/%Y %H:%M:%S')}: {__HORARIO__}')


def registro_tela(driver) -> None:

    global __N_DAILY_REG__

    aux = datetime.datetime.now()
    data = (('0' + str(aux.day) + '_') if aux.day < 10 else (str(aux.day) + '_'))
    data = data + (('0' + str(aux.month) + '_') if aux.month < 10 else (str(aux.month) + '_'))
    data = data + str(aux.year)

    hora = (('0' + str(aux.hour)) if aux.hour < 10 else (str(aux.hour)) + '_')
    hora = hora + (('0' + str(aux.minute)) if aux.minute < 10 else (str(aux.minute)) + '_')
    hora = hora + (('0' + str(aux.second)) if aux.second < 10 else (str(aux.second)))

    main_dir = os.getcwd()
    dir_reg = '.registros'
    dir_reg_daily  = dir_reg + '_' + data
    name_reg = str(__N_DAILY_REG__) + '_' + data + '_' + hora

    os.makedirs(dir_reg, exist_ok=True)
    os.chdir(dir_reg)

    os.makedirs(dir_reg_daily, exist_ok=True)
    os.chdir(dir_reg_daily)
    
    driver.save_screenshot(name_reg+".png")

    os.chdir(main_dir)


def horario_to_str(datetime_obj: datetime) -> str:

    hora_agora = (('0' + str(datetime_obj.hour) + '0') if datetime_obj.hour < 10 else (str(datetime_obj.hour)) + ':')
    hora_agora = hora_agora + (('0' + str(datetime_obj.minute)) if datetime_obj.minute < 10 else (str(datetime_obj.minute)))
    return hora_agora


def adiciona_horario() -> None:

    agora = datetime.datetime.now()

    hora_adicional = agora + datetime.timedelta(minutes=30)
    hora_depois = horario_to_str(hora_adicional)

    __HORARIO_AUX__ = __HORARIO__

    __HORARIO__ = hora_depois
    write_log()


def check_horario() -> None:

    global __HORARIO__
    global __N_DAILY_REG__
    
    agora = datetime.datetime.now()
    hora_agora = (('0' + str(agora.hour)) if agora.hour < 10 else (str(agora.hour)) + ':')
    hora_agora = hora_agora + (('0' + str(agora.minute)) if agora.minute < 10 else (str(agora.minute)))

    if __QTD_PONTOS__ == 4:

        if ((hora_agora <= '07:30' or hora_agora >= '17:45') and __N_DAILY_REG__ != 1):
            
            __N_DAILY_REG__ = 1
            hora_entra = datetime.time(hour=__HH_ENTRADA_1__, minute=0)
            hora_entra = datetime.datetime.combine(datetime.date.today(), hora_entra)
            var_horario = random.randint(0, __VAR_MM__)
            escolhe = random.randint(0, 1)

            if escolhe == 0:

                hora_entra = hora_entra - datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()

            else:
                
                hora_entra = hora_entra + datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()
        
        elif hora_agora < '11:45' and __N_DAILY_REG__ != 2:

            __N_DAILY_REG__ = 2
            hora_sai = datetime.time(hour=__HH_SAIDA_1__, minute=0)
            hora_sai = datetime.datetime.combine(datetime.date.today(), hora_sai)
            var_horario = random.randint(0, __VAR_MM__)
            escolhe = random.randint(0, 1)

            if escolhe == 0:

                hora_sai = hora_sai - datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_sai.hour)) if hora_sai.hour <10 else (str(hora_sai.hour))) + ':')
                aux = aux + (('0' + str(hora_sai.minute)) if hora_sai.minute < 10 else(str(hora_sai.minute)))
                __HORARIO__ = aux
                write_log()

            else:
                
                hora_sai = hora_sai + datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_sai.hour)) if hora_sai.hour <10 else (str(hora_sai.hour))) + ':')
                aux = aux + (('0' + str(hora_sai.minute)) if hora_sai.minute < 10 else(str(hora_sai.minute)))
                __HORARIO__ = aux
                write_log()
        
        elif hora_agora < '12:45' and __N_DAILY_REG__ != 3:
            
            __N_DAILY_REG__ = 3
            hora_entra = datetime.time(hour=__HH_ENTRADA_2__, minute=0)
            hora_entra = datetime.datetime.combine(datetime.date.today(), hora_entra)
            var_horario = random.randint(0, __VAR_MM__)
            escolhe = random.randint(0, 1)

            if escolhe == 0:

                hora_entra = hora_entra - datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()

            else:
                
                hora_entra = hora_entra + datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()
        
        elif hora_agora < '17:45' and __N_DAILY_REG__ != 4:
            
            __N_DAILY_REG__ = 4
            hora_entra = datetime.time(hour=__HH_SAIDA_2__, minute=0)
            hora_entra = datetime.datetime.combine(datetime.date.today(), hora_entra)
            var_horario = random.randint(0, __VAR_MM__)
            escolhe = random.randint(0, 1)

            if escolhe == 0:

                hora_entra = hora_entra - datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()

            else:
                
                hora_entra = hora_entra + datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()

    elif __QTD_PONTOS__ == 2:

        if ((hora_agora <= '07:30' or hora_agora >= '13:45') and __N_DAILY_REG__ != 1):
                    
            __N_DAILY_REG__ = 1
            hora_entra = datetime.time(hour=__HH_ENTRADA_1__, minute=0)
            hora_entra = datetime.datetime.combine(datetime.date.today(), hora_entra)
            var_horario = random.randint(0, __VAR_MM__)
            escolhe = random.randint(0, 1)

            if escolhe == 0:

                hora_entra = hora_entra - datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()

            else:
                
                hora_entra = hora_entra + datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_entra.hour)) if hora_entra.hour <10 else (str(hora_entra.hour))) + ':')
                aux = aux + (('0' + str(hora_entra.minute)) if hora_entra.minute < 10 else(str(hora_entra.minute)))
                __HORARIO__ = aux
                write_log()

        elif hora_agora < '13:45' and __N_DAILY_REG__ != 2:

            __N_DAILY_REG__ = 2
            hora_sai = datetime.time(hour=__HH_SAIDA_1__, minute=0)
            hora_sai = datetime.datetime.combine(datetime.date.today(), hora_sai)
            var_horario = random.randint(0, __VAR_MM__)
            escolhe = random.randint(0, 1)

            if escolhe == 0:

                hora_sai = hora_sai - datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_sai.hour)) if hora_sai.hour <10 else (str(hora_sai.hour))) + ':')
                aux = aux + (('0' + str(hora_sai.minute)) if hora_sai.minute < 10 else(str(hora_sai.minute)))
                __HORARIO__ = aux
                write_log()

            else:
                
                hora_sai = hora_sai + datetime.timedelta(minutes=var_horario)
                aux = ((('0' + str(hora_sai.hour)) if hora_sai.hour <10 else (str(hora_sai.hour))) + ':')
                aux = aux + (('0' + str(hora_sai.minute)) if hora_sai.minute < 10 else(str(hora_sai.minute)))
                __HORARIO__ = aux
                write_log()
            

def registro_ponto() -> None:

    global __ARGS_1__
    global __ARGS_2__
   
    options = webdriver.FirefoxOptions()
#    options.add_argument('--headless=new')
#    options.add_argument('--no-sandbox')
#    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Firefox(options)

    driver.get('http://sistemas08.sisponto.com.br:4000/Sispontoweb/open.do?sys=SPW')

    driver.implicitly_wait(0.5)

    time.sleep(10)      

    iframe = driver.find_element(By.NAME, 'mainform')
    driver.switch_to.frame(iframe)

    usuario   = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[11]/input')
    senha     = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[3]/input')
    btn_login = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[2]/button')

    usuario.send_keys(__ARGS_1__)
    senha.send_keys(__ARGS_2__)
    btn_login.click()

    driver.implicitly_wait(0.5)

    time.sleep(6)

    driver.switch_to.default_content()
    iframe = driver.find_element(By.NAME, 'mainsystem')
    driver.switch_to.frame(iframe)

    iframe2 = driver.find_element(By.NAME, 'mainform')
    driver.switch_to.frame(iframe2)

    time.sleep(6)

    img = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[12]/img')
    menu = driver.find_element(By.XPATH, '/html/body/div[4]/div[2]/div/ul/li[1]/a/span')
    inclusao = driver.find_element(By.XPATH, '/html/body/div[4]/div[2]/div/ul/li[1]/ul/li[1]/a/span')
    registro = driver.find_element(By.ID, '678483')

    ActionChains(driver) \
        .move_to_element(img) \
        .perform()

    time.sleep(1)

    ActionChains(driver) \
        .move_to_element(menu) \
        .perform()

    time.sleep(1)

    ActionChains(driver) \
        .move_to_element(inclusao) \
        .perform()

    time.sleep(1)

    registro.click()

    time.sleep(3)

    driver.switch_to.window(driver.window_handles[1])

    driver.switch_to.default_content()
    iframe_ponto = driver.find_element(By.NAME, 'mainform')
    driver.switch_to.frame(iframe_ponto)

    btn_registro = driver.find_element(By.XPATH, '/html/body/form/div/div[2]/div[2]/div[10]/button')
    btn_registro.click()

    time.sleep(5)

    #registro_tela(driver)

    time.sleep(3)

    driver.close()

    driver.switch_to.window(driver.window_handles[0])

    driver.switch_to.default_content()
    iframe = driver.find_element(By.NAME, 'mainsystem')
    driver.switch_to.frame(iframe)
    iframe2 = driver.find_element(By.NAME, 'mainform')
    driver.switch_to.frame(iframe2)

    btn_close = driver.find_element(By.XPATH, '/html/body/div[5]/img')
    btn_close.click()

#    time.sleep(2)

#    driver.quit()

#    arma_rotina(tipo_horario=0)


def justificativa_ponto() -> None:

    global __ARGS_1__
    global __ARGS_2__
    
    options = webdriver.FirefoxOptions()
#    options.add_argument('--headless=new')
#    options.add_argument('--no-sandbox')
#    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Firefox(options)

    driver.get('http://sistemas08.sisponto.com.br:4000/Sispontoweb/open.do?sys=SPW')

    driver.implicitly_wait(0.5)

    time.sleep(10)      

    iframe = driver.find_element(By.NAME, 'mainform')
    driver.switch_to.frame(iframe)

    usuario   = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[11]/input')
    senha     = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[3]/input')
    btn_login = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[2]/button')

    usuario.send_keys(__ARGS_1__)
    senha.send_keys(__ARGS_2__)
    btn_login.click()

    driver.implicitly_wait(0.5)

    time.sleep(6)

    driver.switch_to.default_content()
    iframe = driver.find_element(By.NAME, 'mainsystem')
    driver.switch_to.frame(iframe)

    iframe2 = driver.find_element(By.NAME, 'mainform')
    driver.switch_to.frame(iframe2)

    time.sleep(6)

    img = driver.find_element(By.XPATH, '/html/body/form/div/div[4]/div[12]/img')
    menu = driver.find_element(By.XPATH, '/html/body/div[4]/div[2]/div/ul/li[1]/a/span')
    inclusao = driver.find_element(By.XPATH, '/html/body/div[4]/div[2]/div/ul/li[1]/ul/li[1]/a/span')
    registro = driver.find_element(By.XPATH, '/html/body/div[4]/div[2]/div/ul/li[1]/ul/li[1]/ul/li[1]')

    ActionChains(driver) \
        .move_to_element(img) \
        .perform()

    time.sleep(3)

    ActionChains(driver) \
        .move_to_element(menu) \
        .perform()

    time.sleep(3)

    ActionChains(driver) \
        .move_to_element(inclusao) \
        .perform()

    time.sleep(3)

    registro.click()

    time.sleep(3)

    driver.switch_to.window(driver.window_handles[1])

    driver.switch_to.default_content()
    iframe_ponto = driver.find_element(By.XPATH, '/html/body/iframe')
    driver.switch_to.frame(iframe_ponto)
  
    horario = driver.find_element(By.NAME, 'WFRInput745226')
    texto   = driver.find_element(By.NAME, 'WFRInput747438')
    botao_s = driver.find_element(By.XPATH, '/html/body/form[1]/div/div[2]/div[2]/div[13]/div[2]/div/button')
    botao_f = driver.find_element(By.XPATH, '/html/body/form[1]/div/div[2]/div[2]/div[15]/button')
           
    texto.send_keys('Sistema estava inoperante, impossibilitando o registro do ponto.')

    time.sleep(2)

    driver.execute_script(
        "arguments[0].value = arguments[1];",
        horario, __HORARIO_AUX__
    )
    
    time.sleep(2)

    botao_s.click()

    time.sleep(2)

    select_element = driver.find_element(By.ID, 'lookupInput')
    select = Select(select_element)
    select.select_by_visible_text('Registro manual')

    time.sleep(2)

    botao_f.click()

    time.sleep(5)

    alerta = WebDriverWait(driver, 10).until(EC.alert_is_present())

    alerta.accept()

    time.sleep(2)

    driver.close()

    time.sleep(2)

    driver.switch_to.window(driver.window_handles[0])
    
    driver.switch_to.default_content()
    iframe = driver.find_element(By.NAME, 'mainsystem')
    driver.switch_to.frame(iframe)
    iframe2 = driver.find_element(By.NAME, 'mainform')
    driver.switch_to.frame(iframe2)

    btn_close = driver.find_element(By.XPATH, '/html/body/div[5]/img')
    btn_close.click()

#    time.sleep(2)

#    driver.quit()

#    arma_rotina(tipo_horario=0)


def main() -> None:

    global __FIRST_TIME__

    if __FIRST_TIME__:

        __FIRST_TIME__ = False 
        getset_args()       
        arma_rotina(tipo_horario=0)

    while True:

        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    
    main()
