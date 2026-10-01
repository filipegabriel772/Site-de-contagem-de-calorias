from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Refeicoes, Metas
from .forms import Refeicao_ia, Definir_metas_form
import ollama
import re



@login_required
def lista_refeicoes(request):
    # Tenta buscar a meta do usuário logado
    try:
        meta_do_usuario = Metas.objects.get(usuario=request.user)
        meta_calorias = meta_do_usuario.meta_calorias
        meta_proteinas = meta_do_usuario.meta_proteinas
    # Se ele for novo, a meta é None
    except Metas.DoesNotExist:
        meta_do_usuario = None
        meta_calorias = 0
        meta_proteinas = 0

    hoje = timezone.now().date()
    refeicoes_hoje = Refeicoes.objects.filter(
        usuario = request.user,
        data = hoje
    )

    # O Banco de dados faz a conta internamente e devolve só o número final
    totais = refeicoes_hoje.aggregate(
        total_cal = Sum('calorias'),
        total_prot = Sum('proteinas')
    )
    # Se o usuário não comeu nada hoje, o banco devolve None. O "or 0" transforma em 0.
    calorias_consumidas = totais['total_cal'] or 0
    proteinas_consumidas = totais['total_prot'] or 0  

    # Cálculo da barra de progresso  
    # Evita o erro de divisão por zero caso a meta seja 0
    pct_calorias = 0
    if meta_calorias > 0:  
        pct_calorias = (calorias_consumidas / meta_calorias) * 100

    pct_proteinas = 0
    if meta_proteinas > 0:
        pct_proteinas = (proteinas_consumidas / meta_proteinas) * 100

    # Prepara um pacote com esses dados para mandar pro HTML
    contexto = {
        'metas': meta_do_usuario,
        'alimentos': refeicoes_hoje,
        'calorias_consumidas': calorias_consumidas,
        'proteinas_consumidas': proteinas_consumidas,
        'pct_calorias': pct_calorias,
        'pct_proteinas': pct_proteinas
    }
    
    # Pede para o Django renderizar (desenhar) o HTML usando esses dados
    return render(request, 'nutricao/lista.html', contexto)


def cadastrar_usuario(request):
    # O usuário enviou os dados do formulário (Método POST)
    if request.method == 'POST':
        # Pega os dados digitados e coloca no fomulário do Django
        formulario = UserCreationForm(request.POST)

        # Se os dados são válidos salva no BD
        if formulario.is_valid():
            formulario.save()
            return redirect('painel') # Redireciona a página inicial
    
    # O usuário apenas acessou a página para ver o formulário (Método GET)
    else:
        # É criado um formulário vazio para ele preencher
        formulario = UserCreationForm()

        contexto = {
            'formulario': formulario
        }

        return render(request, 'nutricao/cadastro.html', contexto)
    

@login_required
def adicionar_refeicao_ia(request):
    # O usuário digitou o que comeu e clicou em SALVAR (POST)
    if request.method == 'POST':
        # Aqui o formulário recebe os dados que vieram da página
        formulario = Refeicao_ia(request.POST)
        # Verifica se o formulário preenchido é válido
        if formulario.is_valid():
            # Pegamos apenas o texto limpo que o usuário digitou
            texto_digitado = formulario.cleaned_data['descricao']
            
            prompt = f"""
            Analise nutricionalmente: {texto_digitado}
    
            Regras estritas:
            1. Você é uma API que fornece dados nutricionais precisos para um banco de dados SQL. O banco de dados aceita apenas valores numéricos únicos.
            2. Retorne SOMENTE e EXCLUSIVAMENTE no padrão: Calorias: X kcal | Proteínas: Y g
            3. Se houver variação de valores (ex: 200-300), calcule a MÉDIA e retorne apenas um número único.
            4. Retorne apenas números inteiros para calorias e decimais (com ponto) para proteínas.
            5. Informe somente a resposta, não é necessário mostrar o raciocíonio para chegar na respota.
            6. É preciso estar exatamente como o padrão mencionado na regra 2, inclusive com o Kcal e g após os números.
            7. Lembre-se, a resposta será utilizado para um cálculo nutricional então tente ser o mais preciso possível conforme na descrição informada
            """

            try:
                info = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
                resposta = info["message"]["content"]

                padrao = r"Calorias:\s*(\d+)\s*kcal\s*\|\s*Proteínas:\s*([\d\.,]+)\s*g"
                match = re.search(padrao, resposta, re.IGNORECASE)

                if match:
                    # Pega o primeiro número encontrado (Calorias) e converte para Inteiro
                    calorias = int(match.group(1))
                    # Pega o segundo número (Proteínas), troca vírgula por ponto (se houver) e vira Decimal
                    proteinas_texto = match.group(2).replace(',', '.') 
                    proteinas = float(proteinas_texto)

                    # Em vez do INSERT INTO, criamos o objeto e ele salva sozinho
                    Refeicoes.objects.create(
                        usuario=request.user,  # Pega automaticamente quem está logado no momento
                        descricao=texto_digitado,
                        calorias=calorias,
                        proteinas=proteinas
                    )
                    
                    # Mandamos um aviso de sucesso verde para a tela
                    messages.success(request, f'Refeição salva! IA calculou: {calorias} kcal e {proteinas}g de proteína.')
                    return redirect('adicionar_ia')

                else:
                    # Se a IA não seguiu o padrão, mandamos um aviso de erro vermelho
                    messages.error(request, "A IA respondeu fora do padrão. Tente descrever a refeição novamente.")
                    print(f"Erro IA: {resposta}") # Mantemos o print só para você investigar depois

            except Exception as error:
                # Se o aplicativo do Ollama estiver fechado, por exemplo
                messages.error(request, "Erro ao conectar com a IA")
                print(f"Erro no sistema: {error}")

    # O usuário acabou de clicar no link para ABRIR a tela (GET)
    else:
        # O usuário apenas abriu a tela vazia (GET)
        # Criando o formulário zerado
        formulario = Refeicao_ia()
    
    # Dando o nome de form para o formulario
    contexto = {'form': formulario}
    return render(request, 'nutricao/adicionarIA.html', contexto)

@login_required
def definir_metas(request):
    # BUSCA NO BANCO: Tenta achar a gaveta de metas desse usuário específico
    try:
        meta_do_usuario = Metas.objects.get(usuario=request.user)
    # Se ele for um usuário novo e nunca definiu metas, a gaveta estará vazia
    except Metas.DoesNotExist:
        meta_do_usuario = None

    # SE O USUÁRIO CLICOU EM "SALVAR" (POST)
    if request.method == 'POST':
        # O 'instance=meta_do_usuario' avisa: "Se já existir uma meta antiga, edite ela. Se não, crie uma nova."
        formulario = Definir_metas_form(request.POST, instance=meta_do_usuario)
        # commit=False significa: "Segura um pouco, não salva no banco ainda!"
        meta_salva = formulario.save(commit=False)  
        # Avisamos ao banco de dados quem é o dono dessa meta
        meta_salva.usuario = request.user    
        # salva no banco de verdade!
        meta_salva.save()
        # mandamos uma mensagem de sucesso para a tela
        messages.success(request, f'Metas salvas com sucesso')

    # SE O USUÁRIO SÓ ABRIU A PÁGINA (GET)
    else:
        # Abre a prancheta limpa ou já preenchida com as metas antigas dele
        formulario = Definir_metas_form(instance=meta_do_usuario)
    
    contexto = {'form': formulario}
    return render(request, 'nutricao/definir-metas.html', contexto)

@login_required
def historico(request):
    print("TODAS AS REFEIÇÕES:")
    print(
        Refeicoes.objects.filter(usuario=request.user).values(
            'id',
            'descricao',
            'data'
        )
    )

    data_filtro = request.GET.get('data')

    if data_filtro:
        registro = Refeicoes.objects.filter(
            usuario = request.user,
            data=data_filtro)
    else:
        registro = Refeicoes.objects.none()

    try:
        meta_do_usuario = Metas.objects.get(usuario=request.user)
        meta_calorias = meta_do_usuario.meta_calorias
        meta_proteinas = meta_do_usuario.meta_proteinas
    # Se ele for novo, a meta é None
    except Metas.DoesNotExist:
        meta_do_usuario = None
        meta_calorias = 0
        meta_proteinas = 0

    # O Banco de dados faz a conta internamente e devolve só o número final
    totais = registro.aggregate(
        total_cal = Sum('calorias'),
        total_prot = Sum('proteinas')
    )
    # Se o usuário não comeu nada hoje, o banco devolve None. O "or 0" transforma em 0.
    calorias_consumidas = totais['total_cal'] or 0
    proteinas_consumidas = totais['total_prot'] or 0  

    # Cálculo da barra de progresso  
    # Evita o erro de divisão por zero caso a meta seja 0
    pct_calorias = 0
    if meta_calorias > 0:  
        pct_calorias = (calorias_consumidas / meta_calorias) * 100

    pct_proteinas = 0
    if meta_proteinas > 0:
        pct_proteinas = (proteinas_consumidas / meta_proteinas) * 100

    # Prepara um pacote com esses dados para mandar pro HTML
    contexto = {
        'metas': meta_do_usuario,
        'alimentos': registro,
        'calorias_consumidas': calorias_consumidas,
        'proteinas_consumidas': proteinas_consumidas,
        'pct_calorias': pct_calorias,
        'pct_proteinas': pct_proteinas
    }

    return render(request, 'nutricao/historico.html', contexto)



