# Estudos-Tracker

Guia do Aplicativo: Estudos Tracker
Descrição do Aplicativo
O Estudos Tracker é um aplicativo de gerenciamento de estudos baseado na técnica Pomodoro. Ele ajuda você a organizar seu tempo de estudo, acompanhar seu progresso semanal e manter a disciplina com alertas sonoros e relatórios de desempenho.

## Funcionalidades do Aplicativo
Pomodoro Timer:

Temporizador configurável para ciclos de foco e pausas.
Alertas sonoros ao final de cada ciclo.
Calendário de Estudos:

Exibe o progresso diário com base no tempo estudado.
Permite editar o estado de cada dia (Estudado, Falhei, etc.).
Resumo Semanal:

Mostra o total de horas estudadas na semana atual e na semana passada.
Exibe mensagens motivacionais com base no desempenho.
Configurações de Tempo:

Personalize os tempos de foco, pausas curtas, pausas longas e a meta semanal.
Minimizar para a Bandeja do Sistema:

O aplicativo pode ser minimizado para a bandeja do sistema.
Menu da bandeja com as opções:
Abrir: Restaura a janela principal.
Sair: Encerra o aplicativo.

Como Usar o Aplicativo

## 1. Iniciar o Temporizador
Clique no botão "Iniciar / Pausar" para começar ou pausar o temporizador.
O temporizador alterna automaticamente entre ciclos de foco e pausas.

## 2. Editar o Estado de um Dia
Clique em um dia no calendário para editar seu estado:
Estudado: Marca o dia como concluído.
Falhei: Marca o dia como não concluído.
Não era pra estudar: Define o dia como neutro.

## 3. Ver o Resumo Semanal
Clique no botão "📊 Resumo Semanal" para abrir o relatório da semana atual e da semana passada.

## 4. Configurar Tempos
Clique no botão "⚙️ Opções" para ajustar os tempos de foco, pausas e a meta semanal.

## 5. Minimizar para a Bandeja
Clique no botão de fechar (X) para minimizar o aplicativo para a bandeja do sistema.
Clique com o botão direito no ícone da bandeja para abrir o menu:
Abrir: Restaura a janela principal.
Sair: Encerra o aplicativo.

## Como Configurar o Aplicativo para Iniciar com o Windows

# Passo 1: Criar um Atalho do Executável
Navegue até a pasta onde o executável do aplicativo está localizado (gerado pelo PyInstaller, geralmente na pasta dist).
Clique com o botão direito no arquivo estudos_tracker.exe e selecione Criar atalho.
# Passo 2: Mover o Atalho para a Pasta de Inicialização
Pressione Win + R para abrir o Executar.
Digite shell:startup e pressione Enter.
Isso abrirá a pasta de inicialização do Windows.
Mova o atalho criado no Passo 1 para esta pasta.
# Passo 3: Testar a Inicialização
Reinicie o computador.
O aplicativo será iniciado automaticamente junto com o Windows.

Estrutura do Código
## 1. Arquivos Necessários
estudos_tracker.py: Código principal do aplicativo.
icon.ico: Ícone do aplicativo.
alarme.mp3: Som do alarme.
dados_estudo.json: Arquivo de dados para salvar o progresso.
## 2. Principais Classes e Funções
App: 
Gerencia a interface principal do aplicativo.
Inclui o calendário, temporizador e botões de controle.
PomodoroTimer:
Gerencia o temporizador Pomodoro.
Alterna entre ciclos de foco e pausas.
AppWithTray:
Adiciona a funcionalidade de minimizar para a bandeja do sistema.
Gerencia o ícone da bandeja e o menu de contexto.
Dicas e Soluções de Problemas
O Alarme Não Toca:

Certifique-se de que o arquivo alarme.mp3 está no mesmo diretório que o executável.
Verifique se o volume do sistema está ativado.
O Aplicativo Não Abre ao Clicar em "Abrir" na Bandeja:

Certifique-se de que o método restaurar_janela está configurado corretamente no código.
Erro ao Salvar Dados:

Verifique se o arquivo dados_estudo.json tem permissões de escrita.
Se o arquivo estiver corrompido, exclua-o para que um novo seja criado automaticamente.
O Aplicativo Não Inicia com o Windows:

Certifique-se de que o atalho está na pasta de inicialização (shell:startup).
Verifique se o executável está acessível no caminho especificado pelo atalho.

# Estudos Tracker

O **Estudos Tracker** é um aplicativo para gerenciar seus estudos com base na técnica Pomodoro. Ele ajuda a organizar seu tempo, acompanhar seu progresso e manter a disciplina.

---

## Configuração

O aplicativo salva os dados de progresso e configurações no seguinte local:

- **Windows**: `%APPDATA%\EstudosTracker\dados_estudo.json`
- **Linux/macOS**: `~/.estudos_tracker/dados_estudo.json`

### Como Editar o Arquivo de Configuração

1. Navegue até o local indicado acima.
2. Abra o arquivo `dados_estudo.json` com um editor de texto (como o **Notepad** ou **VS Code**).
3. Edite os valores conforme necessário. Por exemplo:
   ```json
   {
       "dias": {
           "2025-04-09": {
               "estado": "Estudado",
               "tempo": 7200
           }
       },
       "tempos": {
           "foco": 1500,
           "pausa": 300,
           "pausa_longa": 900,
           "meta_semanal": 36000
       },
       "ciclos": 4
   }
   ```

---

