from __future__ import annotations
from io import BufferedReader

class IndicePrimario:

    valores: list[tuple[int, int]]#id e offset

    def __init__(self):
        self.valores = []

    def adiciona_elemento(self, elemento: tuple[int, int]) -> None:
        '''Adiciona elemento no indice'''
        raise NotImplementedError
    
    def remove_elemento(self, id: str) -> None:
        '''Remove um elemento pelo id'''
        raise NotImplementedError
    
class IndiceSecundario:

    valores: list[tuple[str, int]]#chave e valor
    lista_invertida: ListaInvertida

    def __init__(self, lista_invertida: ListaInvertida):
        self.valores = []
        self.lista_invertida = lista_invertida

    def adiciona_elemento(self, chave: str, id_elemento: int) -> None:
        '''Adiciona elemento no indice'''
        raise NotImplementedError
    
    def remove_elemento(self, chave: str) -> None:
        '''Remove um elemento pela chave'''
        raise NotImplementedError
    
class ListaInvertida:

    valores: list[tuple[int, int, int]]# id, prox_gen, prox_publi

    def __init__(self):
        valores = []

    def adiciona_elemento(self, id_elemento: int) -> None:
        '''Adiciona elemento no indice baseado no id'''
        raise NotImplementedError
    
    def remove_elemento(self, id: int) -> None:
        '''Remove um elemento pelo id'''
        raise NotImplementedError
#contrução de indices

def constroi_indices(nome_arquivo_dados: str) -> None:
    '''
    Constroi baseado no arquivo de dados os arquivos de indice primario (primario.ind) indices secundarios
    (genero.ind, publicadora.ind) e lista invertida (listaInvertida.ind). Os indices secundarios utilizam Late Biding

    :param nome_arquivo_dados: nome do arquivo fonte
    '''
    with open(nome_arquivo_dados, "rb") as dados:

        indice_pri = IndicePrimario()
        lista_invertida = ListaInvertida()
        indice_sec_gen = IndiceSecundario(lista_invertida)
        indice_sec_publi = IndiceSecundario(lista_invertida)
        
        offset = 0
        tam_registro_bytes = dados.read(2)

        while tam_registro_bytes:
            tam_registro = int.from_bytes(tam_registro_bytes, 'little')

            registro_string = dados.read(tam_registro).decode()
            registro = registro_string.split(sep='|')
            registro.pop()#remove o campo vazio

            id_registro = int(registro[0])
            gen_registro = registro[3]
            publi_regsitro = registro[4]

            indice_pri.adiciona_elemento([id_registro, offset])
            indice_sec_gen.adiciona_elemento(gen_registro, id_registro)
            indice_sec_publi.adiciona_elemento(publi_regsitro, id_registro)

            tam_registro_bytes = dados.read(2)
            offset += 2 + tam_registro

    cria_arquivo("primairo.ind", indice_pri)
    cria_arquivo("genero.ind", indice_sec_gen)
    cria_arquivo("publicadora.ind", indice_sec_publi)
    cria_arquivo("listaInvertida.lst", lista_invertida)

def cria_arquivo(nome_arquivo: str, tabela: list[tuple]) -> None:
    '''
    Cria um arquivo com os dados da tabela, se o arquivo já existir ele é sobrescrito
    '''

    with open(nome_arquivo, "wb") as saida:
        
        for registro in tabela:
            registro_str = ""

            for campo in registro:
                registro_str += str(campo) + '|'

            tamanho = len(registro_str)

            saida.write(tamanho.to_bytes(byteorder="little"))
            saida.write(registro_str.encode())


def main() -> None:

    constroi_indices("games.dat")

if __name__ == '__main__':
    main()