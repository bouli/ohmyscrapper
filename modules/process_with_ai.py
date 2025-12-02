import models.urls_manager as urls_manager
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv

load_dotenv()
def process_with_ai():
    url_type = 'linkedin_post'
    df = urls_manager.get_urls_by_url_type_for_ai_process(url_type)

    texts = ""
    for index, row in df.iterrows():
        texts = texts + f"""
        <texto>
        <id>{str(row['id'])}</id>
        {row['description']}
        </texto>
        """
    if texts == "":
        print('no urls to process')
        return

    instructions = """
    <contexto>Esses são textos com 1 ou várias vagas de emprego. Quando há mais de uma vaga em um texto, elas são acompanhadas de suas respectivas urls.</contexto>
    <textos>
    """ + texts + """
    </textos>
    <pergunta>Faça uma lista em `XML` com o número de id de cada texto seguido do nome de cada vaga e, se houver, sua respectiva organização ou empresa na mesma lista. </pergunta>
    <formato_resposta_esperado>
    Se não for possível identificar a organização ou empresa, deixe esta informação em branco.
    Se não for possível identificar a url, deixe esta informação em branco.
    Para cada vaga, mantenha o mesmo idioma em que o respectivo texto está escrito. Responda, sem informações adicionais ou explicaçãop, apenas o texto em `XML` como o exemplo a seguir:
    <vagas>
        <vaga>
            <id>12</id>
            <titulo>Nome da Vaga 12</titulo>
            <contratante>Nome da Empresa 12</contratante>
            <url>http://www.url-vaga-12.com/exemplo</url>
        </vaga>
        <vaga>
            <id>215</id>
            <titulo>Position Name 215</titulo>
            <contratante>Company Name 215</contratante>
            <url>http://www.url-position-215.com/sample</url>
        </vaga>
        <vaga>
            <id>941</id>
            <titulo>Nome da Vaga 941</titulo>
            <contratante>Nome da Empresa 941</contratante>
            <url>http://www.url-empresa-941.com/vaga</url>
        </vaga>
        <vaga>
            <id>85</id>
            <titulo>Nome da Vaga 85</titulo>
            <contratante></contratante>
            <url></url>
        </vaga>
    </vagas>

    </formato_resposta_esperado>
    """
    model = "gemini-2.5-flash"
    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client()
    print("starting...")
    response = client.models.generate_content(
        model=model, contents=instructions
    )
    response = str(response.text)
    urls_manager.add_ai_log(instructions=instructions, response=response, model=model)
    print(response)
    print('^^^^^^')
    soup = BeautifulSoup(response, 'html.parser')
    for vaga in soup.find_all("vaga"):

        url = urls_manager.get_url_by_id(vaga.find("id").text)
        if len(url) > 0:
            url = url.iloc[0]

        h1 = vaga.find("titulo").text
        if vaga.find("contratante").text != 'desconhecido' and vaga.find("contratante").text != '':
            h1 = h1 + " - " + vaga.find("contratante").text
        if url['description_links'] > 1 and vaga.find("id").text != "":
            urls_manager.set_url_h1(vaga.find("url").text, h1)
            urls_manager.set_url_ai_processed_by_url(vaga.find("url").text)
            urls_manager.touch_url(vaga.find("url").text)
            print('-- child updated -- ' , vaga.find("url").text , h1)
        elif url['description_links'] <= 1:
            urls_manager.set_url_h1_by_id(vaga.find("id").text, h1)
            urls_manager.set_url_ai_processed_by_id(vaga.find("id").text)
            print('-- parent updated -- ' , url['url'] , h1)
        else:
            print('-- not updated -- ' , url['url'] , h1)

    print('ending...')
    return

#TODO: Separate gemini from basic function
def _process_with_gemini(model,instructions):
    response = """"""
    return response
