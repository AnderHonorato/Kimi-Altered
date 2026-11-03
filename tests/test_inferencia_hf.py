"""Testes sem rede e sem consumo de creditos."""
import importlib.util
import io
import pathlib
import unittest
from contextlib import redirect_stdout
from unittest import mock
from urllib.error import HTTPError

CAMINHO = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "inferencia_hf.py"
especificacao = importlib.util.spec_from_file_location("inferencia_hf", CAMINHO)
modulo = importlib.util.module_from_spec(especificacao)
especificacao.loader.exec_module(modulo)


class TesteHuggingFace(unittest.TestCase):
    def test_verificar_consulta_metadados_nao_pesos(self):
        dados = {"id": "moonshotai/Kimi-K3", "siblings": [
            {"rfilename": "model-00001-of-000096.safetensors"},
            {"rfilename": "config.json"},
        ]}
        with mock.patch.object(modulo, "requisitar_json", return_value=dados) as requisicao:
            with redirect_stdout(io.StringIO()) as saida:
                self.assertEqual(modulo.verificar(), 0)
            self.assertIn("1 (esperados: 96)", saida.getvalue())
            self.assertEqual(requisicao.call_args.args[0], modulo.URL_METADADOS)
            self.assertNotIn(".safetensors", requisicao.call_args.args[0])

    def test_envio_dados_e_limite(self):
        retorno = {"choices": [{"message": {"content": "Olá!"}}]}
        with mock.patch.object(modulo, "requisitar_json", return_value=retorno) as req:
            self.assertEqual(modulo.enviar([{"role": "user", "content": "oi"}], "privado", 32), "Olá!")
            parametros = req.call_args.kwargs
            self.assertEqual(parametros["metodo"], "POST")
            self.assertEqual(parametros["dados"]["model"], "moonshotai/Kimi-K3:cheapest")
            self.assertEqual(parametros["dados"]["max_tokens"], 32)

    def test_exige_consentimento(self):
        with self.assertRaises(SystemExit) as resultado:
            modulo.principal(["--chat"])
        self.assertEqual(resultado.exception.code, 2)

    def test_formato_de_resposta(self):
        dados = {"choices": [{"message": {"content": [
            {"type": "text", "text": "Resposta"},
        ]}}]}
        self.assertEqual(modulo.texto_resposta(dados), "Resposta")

    def test_erro_nao_vaza_token(self):
        erro = HTTPError(modulo.URL_INFERENCIA, 401, "Sem autorizacao", {}, None)
        with mock.patch.object(modulo.urllib.request, "urlopen", side_effect=erro):
            with self.assertRaises(RuntimeError) as resultado:
                modulo.requisitar_json(modulo.URL_INFERENCIA, metodo="POST",
                                       dados={"messages": []}, token="token-secreto")
        self.assertNotIn("token-secreto", str(resultado.exception))


if __name__ == "__main__":
    unittest.main()
