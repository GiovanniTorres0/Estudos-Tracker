import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import json
import os
import pygame
import threading
import time
import calendar
import locale
import random  # Adicione a importação do módulo random
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import sys
import msvcrt  # Para garantir uma única instância no Windows

# Define o caminho dos arquivos
if getattr(sys, 'frozen', False):  # Verifica se está rodando como executável
    BASE_PATH = sys._MEIPASS  # Diretório temporário onde os arquivos são extraídos
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))  # Diretório do script

ICON_PATH = os.path.join(BASE_PATH, "icon.ico")
ALARME_SOM = os.path.join(BASE_PATH, "alarme.mp3")

# Define o caminho para o diretório de dados do usuário
if sys.platform == "win32":
    DATA_DIR = os.path.join(os.getenv("APPDATA"), "EstudosTracker")
else:
    DATA_DIR = os.path.join(os.path.expanduser("~"), ".estudos_tracker")

DADOS_ARQUIVO = os.path.join(DATA_DIR, "dados_estudo.json")

# Cria o diretório, se não existir
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

TEMPO_PADRAO = {
    "foco": 25 * 60,
    "pausa": 5 * 60,
    "pausa_longa": 15 * 60,
    "meta_semanal": 10 * 60 * 60
}

dados = {
    "dias": {},
    "tempos": TEMPO_PADRAO,
    "ciclos": 0
}

mensagem_atual = {"semana": None, "mensagem": None}

def carregar_dados():
    if not os.path.exists(DADOS_ARQUIVO):
        with open(DADOS_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)  # Cria o arquivo com os dados padrão
    else:
        with open(DADOS_ARQUIVO, "r", encoding="utf-8") as f:
            dados.update(json.load(f))

def salvar_dados():
    with open(DADOS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def tocar_alarme():
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(ALARME_SOM)
        pygame.mixer.music.play()
    except Exception as e:
        print("Erro ao tocar alarme:", e)

def verificar_meta_diaria():
    """Verifica se a meta diária foi atingida e marca o dia como 'Não Estudado' se necessário."""
    dia_atual = datetime.now().strftime("%Y-%m-%d")
    registro = dados["dias"].setdefault(dia_atual, {"estado": "-", "tempo": 0})
    meta_diaria = dados["tempos"]["meta_semanal"] // 7  # Divide a meta semanal por 7 para obter a meta diária

    if registro["tempo"] < meta_diaria and registro["estado"] == "-":
        registro["estado"] = "Não Estudado"
        salvar_dados()

class PomodoroTimer:
    def __init__(self, app, update_callback):
        self.app = app  # Referência à instância da classe App
        self.update_callback = update_callback
        self.tempo_total = dados["tempos"]["foco"]
        self.tempo_restante = self.tempo_total
        self.executando = False
        self.tipo_atual = "foco"
        self.thread = None

    def iniciar(self):
        if not self.executando:
            self.executando = True
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def pausar(self):
        self.executando = False

    def resetar(self):
        if not self.executando and self.tempo_restante == dados["tempos"]["foco"]:
            # Marca o dia como "Falha" se o Pomodoro não foi iniciado
            dia = datetime.now().strftime("%Y-%m-%d")
            registro = dados["dias"].setdefault(dia, {"estado": "-", "tempo": 0})
            if registro["estado"] == "-":  # Apenas atualiza se o estado for vazio
                registro["estado"] = "Falhei"
            salvar_dados()

        self.executando = False
        self.tempo_restante = dados["tempos"][self.tipo_atual]
        self.update_callback(self.formatar_tempo(self.tempo_restante), self.tipo_atual)

        # Verifica a meta diária
        verificar_meta_diaria()

    def run(self):
        tempo_inicial = self.tempo_restante  # Salva o tempo inicial para calcular o tempo estudado

        while self.tempo_restante > 0 and self.executando:
            mins, secs = divmod(self.tempo_restante, 60)
            self.update_callback(f"{mins:02d}:{secs:02d}", self.tipo_atual)
            time.sleep(1)
            self.tempo_restante -= 1

        if self.tempo_restante <= 0:
            tocar_alarme()

            if self.tipo_atual == "foco":
                dados["ciclos"] += 1
                tempo_estudado = tempo_inicial  # Calcula o tempo efetivamente estudado
                dia = datetime.now().strftime("%Y-%m-%d")
                registro = dados["dias"].setdefault(dia, {"estado": "-", "tempo": 0})

                # Marca o dia como "Estudado" e adiciona o tempo
                registro["tempo"] += tempo_estudado
                if registro["estado"] == "-":  # Apenas atualiza se o estado for vazio
                    registro["estado"] = "Estudado"
                salvar_dados()

                # Atualiza o calendário imediatamente
                self.app.atualizar_calendario()

            if self.tipo_atual == "foco":
                self.tipo_atual = "pausa_longa" if dados["ciclos"] % 4 == 0 else "pausa"
            else:
                self.tipo_atual = "foco"

            self.tempo_restante = dados["tempos"][self.tipo_atual]
            self.executando = False
            self.update_callback(self.formatar_tempo(self.tempo_restante), self.tipo_atual)

    def alternar(self):
        if (self.executando):
            self.pausar()
        else:
            self.iniciar()

    def formatar_tempo(self, segundos, tipo=None):
        mins, secs = divmod(segundos, 60)
        return f"{mins:02d}:{secs:02d}"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Estudos")
        self.root.geometry("750x700")
        self.root.resizable(False, False)
        self.root.iconbitmap(ICON_PATH)
        self.timer = PomodoroTimer(self, self.atualizar_timer)  # Passa a instância de App

        self.mes_atual = datetime.today().month
        self.ano_atual = datetime.today().year

        self.criar_widgets()
        carregar_dados()
        self.atualizar_calendario()

    def criar_widgets(self):
        # Frame superior
        self.frame_cima = tk.Frame(self.root, bg="#f0f0f0")
        self.frame_cima.pack(pady=10, fill="x")

        # Botão de opções
        self.btn_opcoes = tk.Button(
            self.frame_cima,
            text="⚙️ Opções",
            command=self.abrir_opcoes,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            relief="flat",
            activebackground="#45a049",
            cursor="hand2"
        )
        self.btn_opcoes.grid(row=0, column=0, padx=10)

        # Timer
        self.label_timer = tk.Label(
            self.root,
            text="25:00",
            font=("Arial", 48, "bold"),
            bg="#ffffff",
            fg="#333333"
        )
        self.label_timer.pack(pady=20)

        # Status do timer
        self.label_status = tk.Label(
            self.root,
            text="Foco",
            font=("Arial", 16, "italic"),
            bg="#ffffff",
            fg="#666666"
        )
        self.label_status.pack()

        # Botão de iniciar/pausar
        self.btn_iniciar = tk.Button(
            self.root,
            text="Iniciar / Pausar",
            command=self.timer.alternar,
            font=("Arial", 14),
            bg="#2196F3",
            fg="white",
            relief="flat",
            activebackground="#1e88e5",
            cursor="hand2"
        )
        self.btn_iniciar.pack(pady=10)

        # Botão para abrir o resumo semanal
        self.btn_semana = tk.Button(
            self.root,
            text="📊 Resumo Semanal",
            command=self.abrir_resumo_semana,
            font=("Arial", 14),
            bg="#FF9800",
            activebackground="#fb8c00",
            cursor="hand2"
        )
        self.btn_semana.pack(pady=10)

        # Calendário
        self.frame_calendario = tk.Frame(self.root, bg="#ffffff")
        self.frame_calendario.pack(pady=20, fill="both", expand=True)

    def abrir_resumo_semana(self):
        x = self.root.winfo_x() + 60
        y = self.root.winfo_y() + 60
        win = tk.Toplevel(self.root)
        win.title("Resumo da Semana")
        win.geometry(f"550x600+{x}+{y}")

        hoje = datetime.now().date()
        inicio_semana = hoje - timedelta(days=(hoje.weekday()))  # Segunda-feira da semana atual
        dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]
        total_tempo = 0
        faltas = 0

        # Título da Semana Atual
        tk.Label(win, text="Resumo da Semana Atual", font=("Arial", 14, "bold")).pack(pady=10)

        # Cria uma tabela para exibir os dados da semana atual
        tree = ttk.Treeview(win, columns=("Dia", "Horas Estudadas", "Estado"), show="headings", height=8)
        tree.heading("Dia", text="Dia")
        tree.heading("Horas Estudadas", text="Horas Estudadas")
        tree.heading("Estado", text="Estado")
        tree.column("Dia", width=100, anchor="center")
        tree.column("Horas Estudadas", width=150, anchor="center")
        tree.column("Estado", width=150, anchor="center")
        tree.pack(pady=10, fill="x")

        # Nomes dos dias da semana em português
        nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        for dia in dias_semana:
            data_str = dia.strftime("%Y-%m-%d")
            info = dados["dias"].get(data_str, {})
            tempo = info.get("tempo", 0)
            estado = info.get("estado", "-")
            horas = tempo // 3600
            minutos = (tempo % 3600) // 60
            total_tempo += tempo

            # Conta as faltas
            if estado == "Falhei":
                faltas += 1

            # Define o estado como "Estudado" ou "Não Estudado"
            estado_formatado = "Estudado" if estado == "Estudado" else "Não Estudado"

            # Adiciona os dados na tabela
            tree.insert("", "end", values=(
                f"{nomes_dias[dia.weekday()]} {dia.strftime('%d/%m')}",
                f"{horas}h {minutos}m",
                estado_formatado
            ))

        # Exibe o total de horas estudadas e a meta semanal
        meta = dados["tempos"]["meta_semanal"]
        horas_totais = total_tempo // 3600
        minutos_totais = (total_tempo % 3600) // 60
        horas_restantes = (meta - total_tempo) // 3600
        minutos_restantes = ((meta - total_tempo) % 3600) // 60
        porcentagem = int((total_tempo / meta) * 100)

        resumo_atual = (
            f"Total: {horas_totais}h {minutos_totais}m\n"
            f"Meta semanal: {porcentagem}%\n"
            f"Horas restantes: {horas_restantes}h {minutos_restantes}m"
        )
        tk.Label(win, text=resumo_atual, font=("Arial", 12, "bold")).pack(pady=10)

        # Separador visual
        tk.Label(win, text="-" * 50, font=("Arial", 10), fg="gray").pack(pady=10)

        # Título da Semana Passada
        tk.Label(win, text="Resumo da Semana Passada", font=("Arial", 14, "bold")).pack(pady=10)

        # Resumo da semana passada
        inicio_semana_passada = inicio_semana - timedelta(days=7)
        dias_semana_passada = [inicio_semana_passada + timedelta(days=i) for i in range(7)]
        total_tempo_passado = sum(
            dados["dias"].get(dia.strftime("%Y-%m-%d"), {}).get("tempo", 0) for dia in dias_semana_passada
        )
        horas_totais_passado = total_tempo_passado // 3600
        minutos_totais_passado = (total_tempo_passado % 3600) // 60
        horas_pendentes_passado = (meta - total_tempo_passado) // 3600

        # Determina o status da semana passada
        if total_tempo_passado >= meta:
            status = "SUCESSO"
            cor_status = "green"
            mensagem = self.obter_mensagem_motivacional(sucesso=True)
        else:
            status = "FRACASSO"
            cor_status = "red"
            mensagem = self.obter_mensagem_motivacional(sucesso=False)

        resumo_passado = (
            f"Meta: {meta // 3600}h\n"
            f"Horas estudadas: {horas_totais_passado}h {minutos_totais_passado}m\n"
            f"Horas pendentes: {horas_pendentes_passado}h"
        )
        tk.Label(win, text=resumo_passado, font=("Arial", 10, "italic")).pack(pady=5)
        tk.Label(win, text=status, font=("Arial", 14, "bold"), fg=cor_status).pack(pady=5)
        tk.Label(win, text=mensagem, font=("Arial", 10), wraplength=500, justify="center").pack(pady=10)

        # Botão para fechar a janela
        tk.Button(win, text="Fechar", command=win.destroy).pack(pady=5)

    def obter_mensagem_motivacional(self, sucesso):
        global mensagem_atual  # Declara que estamos usando a variável global

        # Lista de mensagens positivas e negativas
        mensagens_sucesso = [
            "Parabéns! Você está cada vez mais perto dos seus objetivos!",
            "Ótimo trabalho! Continue assim e você alcançará grandes coisas.",
            "Você está no caminho certo. Mantenha o foco e a determinação!",
            "Incrível! Cada esforço está valendo a pena.",
            "Você provou que a disciplina é a chave para o sucesso!",
            "Mais uma semana concluída com sucesso. Continue avançando!",
            "Seu progresso é inspirador. Não pare agora!",
            "Você é a prova de que a consistência traz resultados.",
            "Excelente! Você está construindo um futuro brilhante.",
            "Sucesso é a soma de pequenos esforços repetidos diariamente. Continue assim!"
        ]

        mensagens_fracasso = [
            "Não desista! Use esta semana como aprendizado para melhorar.",
            "Fracassos fazem parte do caminho. Levante-se e tente novamente!",
            "Você pode fazer melhor! Acredite no seu potencial e continue tentando.",
            "Cada dia é uma nova chance de recomeçar. Não desista agora!",
            "Fracassar não é o fim, é apenas uma lição para o próximo passo.",
            "Você é mais forte do que imagina. Não deixe uma semana ruim te parar.",
            "O importante é continuar tentando. Grandes conquistas levam tempo.",
            "Não se preocupe com o fracasso, preocupe-se em não tentar novamente.",
            "A jornada é longa, mas cada passo conta. Continue caminhando!",
            "Você não falhou, apenas encontrou uma maneira de melhorar. Recomece!"
        ]

        # Calcula o número da semana atual
        semana_atual = datetime.now().isocalendar()[1]

        # Verifica se a mensagem já foi definida para a semana atual
        if mensagem_atual["semana"] != semana_atual:
            # Escolhe uma nova mensagem aleatória com base no sucesso ou fracasso
            if sucesso:
                mensagem_atual["mensagem"] = random.choice(mensagens_sucesso)
            else:
                mensagem_atual["mensagem"] = random.choice(mensagens_fracasso)
            mensagem_atual["semana"] = semana_atual

        return mensagem_atual["mensagem"]

    def atualizar_timer(self, tempo, tipo):
        self.label_timer.config(text=tempo)
        status = {
            "foco": "Foco",
            "pausa": "Pausa Curta",
            "pausa_longa": "Pausa Longa"
        }
        self.label_status.config(text=status.get(tipo, ""))

    def abrir_opcoes(self):
        x = self.root.winfo_x() + 100
        y = self.root.winfo_y() + 100
        win = tk.Toplevel(self.root)
        win.title("Opções de Tempo")
        win.geometry(f"300x300+{x}+{y}")

        def salvar_tempos():
            try:
                dados["tempos"]["foco"] = int(entry_foco.get()) * 60
                dados["tempos"]["pausa"] = int(entry_pausa.get()) * 60
                dados["tempos"]["pausa_longa"] = int(entry_pausa_longa.get()) * 60
                dados["tempos"]["meta_semanal"] = int(entry_meta.get()) * 3600
                salvar_dados()
                self.timer.resetar()
                win.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Insira apenas números inteiros.")

        tk.Label(win, text="Foco (min):").pack()
        entry_foco = tk.Entry(win)
        entry_foco.insert(0, str(dados["tempos"]["foco"] // 60))
        entry_foco.pack()

        tk.Label(win, text="Pausa Curta (min):").pack()
        entry_pausa = tk.Entry(win)
        entry_pausa.insert(0, str(dados["tempos"]["pausa"] // 60))
        entry_pausa.pack()

        tk.Label(win, text="Pausa Longa (min):").pack()
        entry_pausa_longa = tk.Entry(win)
        entry_pausa_longa.insert(0, str(dados["tempos"]["pausa_longa"] // 60))
        entry_pausa_longa.pack()

        tk.Label(win, text="Meta Semanal (horas):").pack()
        entry_meta = tk.Entry(win)
        entry_meta.insert(0, str(dados["tempos"]["meta_semanal"] // 3600))
        entry_meta.pack()

        tk.Button(win, text="Salvar", command=salvar_tempos).pack(pady=10)

    def abrir_seletor_data(self):
        x = self.root.winfo_x() + 120
        y = self.root.winfo_y() + 120
        win = tk.Toplevel(self.root)
        win.title("Selecionar Mês e Ano")
        win.geometry(f"250x200+{x}+{y}")

        # Lista de nomes dos meses
        nomes_meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]

        tk.Label(win, text="Mês:").pack()
        combo_mes = ttk.Combobox(win, values=nomes_meses)
        combo_mes.set(nomes_meses[self.mes_atual - 1])  # Define o mês atual
        combo_mes.pack()

        tk.Label(win, text="Ano:").pack()
        combo_ano = ttk.Combobox(win, values=list(range(2000, 2101)))
        combo_ano.set(self.ano_atual)
        combo_ano.pack()

        def aplicar():
            try:
                self.mes_atual = nomes_meses.index(combo_mes.get()) + 1  # Converte o nome do mês para número
                self.ano_atual = int(combo_ano.get())
                self.atualizar_calendario()
                win.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Selecione valores válidos.")

        tk.Button(win, text="Aplicar", command=aplicar).pack(pady=10)

    def atualizar_calendario(self):
        # Limpa o frame do calendário antes de atualizá-lo
        for widget in self.frame_calendario.winfo_children():
            widget.destroy()

        # Adiciona o botão central para selecionar o mês e o ano
        nav_frame = tk.Frame(self.frame_calendario, bg="#ffffff")
        nav_frame.grid(row=0, column=0, columnspan=7, pady=5, sticky="ew")

        # Exibe o mês com a primeira letra maiúscula
        nome_mes = datetime(self.ano_atual, self.mes_atual, 1).strftime("%B").capitalize()
        btn_mes_ano = tk.Button(
            nav_frame,
            text=f"{nome_mes} {self.ano_atual}",
            font=("Arial", 14, "bold"),
            command=self.abrir_seletor_data,
            relief="flat",
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            cursor="hand2"
        )
        btn_mes_ano.pack()

        # Adiciona os nomes dos dias da semana
        dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for i, nome in enumerate(dias_semana):
            tk.Label(
                self.frame_calendario,
                text=nome,
                font=("Arial", 10, "bold"),
                bg="#ffffff",
                fg="#333333"
            ).grid(row=1, column=i, sticky="nsew")

        # Configura as colunas para expandirem proporcionalmente
        for i in range(7):
            self.frame_calendario.columnconfigure(i, weight=1)

        # Cria um calendário para o mês e ano atuais
        cal = calendar.Calendar(firstweekday=0)  # Começa na segunda-feira
        dias_mes = list(cal.itermonthdays(self.ano_atual, self.mes_atual))  # Converte o gerador em uma lista

        # Data atual
        hoje = datetime.now().date()

        # Adiciona os dias ao calendário
        for i, dia in enumerate(dias_mes):
            if dia == 0:
                # Dias fora do mês atual
                tk.Label(self.frame_calendario, text="", width=4, bg="#ffffff").grid(row=(i // 7) + 2, column=i % 7, sticky="nsew")
            else:
                data = datetime(self.ano_atual, self.mes_atual, dia).date()
                estado = dados["dias"].get(data.strftime("%Y-%m-%d"), {}).get("estado", "-")
                tempo = dados["dias"].get(data.strftime("%Y-%m-%d"), {}).get("tempo", 0)
                horas = tempo // 3600
                minutos = (tempo % 3600) // 60

                cor = "green" if estado == "Estudado" else "red" if estado == "Falhei" else "gray"
                bg_cor = "#e8f5e9" if data == hoje else "#ffffff"

                btn = tk.Button(
                    self.frame_calendario,
                    text=f"{dia}\n{horas}h {minutos}m",
                    bg=bg_cor,
                    fg=cor,
                    relief="flat",
                    width=4,
                    height=2,
                    command=lambda d=data.strftime("%Y-%m-%d"): self.editar_estado_dia(d)
                )
                btn.grid(row=(i // 7) + 2, column=(i % 7), sticky="nsew")

        # Configura as linhas para expandirem proporcionalmente
        for i in range((len(dias_mes) // 7) + 2):
            self.frame_calendario.rowconfigure(i, weight=1)

    def mes_anterior(self):
        if self.mes_atual == 1:
            self.mes_atual = 12
            self.ano_atual -= 1
        else:
            self.mes_atual -= 1
        self.atualizar_calendario()

    def abrir_desempenho_semanal(self):
        x = self.root.winfo_x() + 60
        y = self.root.winfo_y() + 60
        win = tk.Toplevel(self.root)
        win.title("Desempenho Semanal")
        win.geometry(f"400x300+{x}+{y}")

        hoje = datetime.now().date()
        dias_semana = [hoje - timedelta(days=i) for i in range(7)]
        total_tempo = 0

        for dia in dias_semana:
            data_str = dia.strftime("%Y-%m-%d")
            info = dados["dias"].get(data_str, {})
            tempo = info.get("tempo", 0)
            estado = info.get("estado", "-")
            horas = tempo // 3600
            minutos = (tempo % 3600) // 60
            total_tempo += tempo
            texto = f"{dia.strftime('%a %d/%m')}: {horas}h {minutos}m - {estado}"
            tk.Label(win, text=texto, anchor="w", justify="left").pack(fill="x")

        meta = dados["tempos"]["meta_semanal"]
        horas_totais = total_tempo // 3600
        minutos_totais = (total_tempo % 3600) // 60
        porcentagem = int((total_tempo / meta) * 100)

        resumo = f"\nTotal: {horas_totais}h {minutos_totais}m\nMeta semanal: {porcentagem}%"
        tk.Label(win, text=resumo, font=("Arial", 12, "bold")).pack(pady=10)

    def editar_estado_dia(self, data):
        dia_atual = datetime.now().strftime("%Y-%m-%d")
        if data != dia_atual:
            messagebox.showerror("Erro", "Você só pode editar o estado do dia atual.")
            return

        x = self.root.winfo_x() + 100
        y = self.root.winfo_y() + 100
        win = tk.Toplevel(self.root)
        win.title("Editar Estado do Dia")
        win.geometry(f"250x150+{x}+{y}")

        def definir_estado(estado):
            dia = dados["dias"].setdefault(data, {"estado": "-", "tempo": 0})
            dia["estado"] = estado
            salvar_dados()
            self.atualizar_calendario()  # Atualiza o calendário imediatamente
            win.destroy()

        tk.Label(win, text=f"Data: {data}").pack(pady=10)
        tk.Button(win, text="Estudado", command=lambda: definir_estado("Estudado")).pack(fill="x")
        tk.Button(win, text="Falhei", command=lambda: definir_estado("Falhei")).pack(fill="x")
        tk.Button(win, text="Não era pra estudar", command=lambda: definir_estado("-")).pack(fill="x")

class AppWithTray(App):
    def __init__(self, root):
        super().__init__(root)
        self.root.iconbitmap(ICON_PATH)  # Define o ícone da barra de tarefas
        self.root.protocol("WM_DELETE_WINDOW", self.minimizar_para_bandeja)
        self.tray_icon = None  # Inicializa o ícone da bandeja como None
        self.tray_thread = None  # Thread para o ícone da bandeja

    def minimizar_para_bandeja(self):
        """Minimiza o aplicativo para a bandeja do sistema."""
        self.root.withdraw()  # Oculta a janela principal
        if not self.tray_icon:  # Cria o ícone da bandeja apenas uma vez
            self.criar_icone_bandeja()

    def criar_icone_bandeja(self):
        """Cria o ícone da bandeja do sistema."""
        # Carrega o ícone para a bandeja
        try:
            image = Image.open(ICON_PATH)  # Certifique-se de que o arquivo icon.ico está no mesmo diretório
        except FileNotFoundError:
            # Cria um ícone simples caso o arquivo não seja encontrado
            image = Image.new("RGB", (64, 64), "green")
            draw = ImageDraw.Draw(image)
            draw.rectangle((16, 16, 48, 48), fill="white")

        # Define o menu da bandeja com as opções "Abrir" e "Sair"
        menu = Menu(
            MenuItem("Abrir", self.restaurar_janela),
            MenuItem("Sair", self.sair)
        )

        # Cria o ícone da bandeja
        self.tray_icon = Icon(
            "Estudos Tracker",
            image,
            "Estudos Tracker",
            menu
        )

        # Executa o ícone da bandeja em uma thread separada
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def restaurar_janela(self, icon=None, item=None):
        """Restaura a janela principal do aplicativo."""
        if self.tray_icon:
            self.tray_icon.visible = True  # Mantém o ícone visível
        self.root.deiconify()  # Restaura a janela principal
        self.root.lift()  # Garante que a janela fique em primeiro plano

    def sair(self, icon=None, item=None):
        """Encerra o aplicativo completamente."""
        if self.tray_icon:
            self.tray_icon.stop()  # Para o ícone da bandeja
        self.root.destroy()  # Fecha a janela principal
        exit()


# Define o caminho para o arquivo de bloqueio no diretório de dados do usuário
APP_LOCK = os.path.join(DATA_DIR, ".app.lock")

# Garantir que apenas uma instância do aplicativo seja executada
def verificar_instancia_unica():
    global lock_file  # Declara a variável global no início da função
    try:
        # No Windows, usamos msvcrt para criar um bloqueio
        lock_file = open(APP_LOCK, "w")
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        messagebox.showerror("Erro", "O aplicativo já está em execução.")
        sys.exit()


if __name__ == "__main__":
    verificar_instancia_unica()  # Garante que apenas uma instância seja executada
    carregar_dados()
    root = tk.Tk()
    app = AppWithTray(root)
    root.mainloop()
