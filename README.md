# EchoClip

EchoClip é uma aplicação "cloud-native" de Text-to-Speech (TTS) para área de transferência, utilizando a API do Google Gemini 2.5 Flash Preview TTS.

## Funcionalidades

- **Clipboard TTS**: Lê automaticamente o texto copiado para a área de transferência ao pressionar uma tecla de atalho.
- **Key Rotation**: Gerencia múltiplas chaves de API para contornar limites de taxa (Rate Limits).
- **Áudio Premium**: Utiliza as vozes de alta qualidade do Gemini (padrão: Enceladus).
- **Systemd Service**: Pode rodar em segundo plano como um serviço do sistema.

## Pré-requisitos do Sistema (Linux/Ubuntu)

Antes de instalar, você precisa de algumas bibliotecas do sistema:

```bash
sudo apt update
sudo apt install xclip portaudio19-dev
```

---

## Instalação (Para Usuários)

A maneira recomendada de usar o EchoClip é através do `pipx`, que instala a ferramenta em um ambiente isolado.

1.  **Instale o EchoClip:**
    ```bash
    pipx install git+https://github.com/ayrtondouglas/echoclip.git
    ```

2.  **Configuração Inicial:**
    Execute o comando de inicialização. Ele irá pedir suas chaves de API e configurar o serviço de sistema (opcional).
    ```bash
    echoclip init
    ```
    *Responda `y` quando perguntado sobre o "systemd user service" para que o EchoClip inicie com o sistema.*

3.  **Usando:**
    - Se você instalou o serviço, ele já está rodando! Basta copiar um texto e pressionar **`F7`**.
    - Se preferir rodar manualmente: `echoclip start`

---

## Instalação (Para Desenvolvedores)

Se você quer contribuir com o código ou modificar o projeto:

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/ayrtondouglas/echoclip.git
    cd echoclip
    ```

2.  **Instale com Poetry:**
    ```bash
    poetry install
    ```

3.  **Rodando em desenvolvimento:**
    ```bash
    poetry run echoclip init
    poetry run echoclip start
    ```

## Configuração

O arquivo de configuração é criado automaticamente em `~/.config/echoclip/config.toml`.
Você pode editá-lo para mudar a voz, atalhos ou velocidade do áudio.

Exemplo de opções:
- `voice_id`: "Enceladus" (padrão), "Puck", "Charon", "Kore", "Fenrir".
- `hotkey`: `<f7>`, `<ctrl>+<alt>+s`.
