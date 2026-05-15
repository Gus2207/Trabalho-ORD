from __future__ import annotations
from io import BufferedReader
from struct import pack, unpack

FORMAT_INDICE_PRIMARIO = 'HH'
TAM_FORMAT_INDICE_PRIMARIO = 4

class IndicePrimario:

    indices: list[tuple[int, int]]#id e offset

    def __init__(self):
        self.indices = []

    def busca_elemento_indice(self, id: int) -> int | None:
        '''Retorna o indice de um elemento na lista, baseado em seu id.
        Retorna None se não encotrar.'''
        i = 0
        while i < len(self.indices) - 1:
            if id == self.indices[i][0]:
                return i
            i += 1
        
        return None
    
    def busca_elemento_offset(self, id: int) -> int | None:
        '''Retorna o offset de um elemento pelo seu id. Retorna None se não encontrar.'''
        ind_elem = self.busca_elemento_indice(id)
        if ind_elem is None:
            return None
        return self.indices[ind_elem][1]

    def adiciona_elemento(self, elemento: tuple[int, int]) -> None:
        '''Adiciona elemento no indice'''
        #insere ordenado
        indices = self.indices
        indices.append(elemento)
        
        i = len(indices) - 1
        pos_correta = False
        while i > 0 and not pos_correta:
            if indices[i] < indices[i-1]:
                indices[i], indices[i-1] = indices[i-1], indices[i]
            else:
                pos_correta = True
            i -= 1
    
    def remove_elemento(self, id: int) -> None:
        '''Remove um elemento pelo id. Se não encontrar, não faz nada.'''
        ind_elem = self.busca_elemento_indice(id)
        if ind_elem is None:
            return
        
        for i in range(ind_elem, len(self.indices)):
            self.indices[i] = self.indices[i+1]
    
    def cria_arquivo(self, nome_saida: str) -> None:
        '''Cria um arquivo binário com os dados do indice'''
        with open(nome_saida, 'wb') as saida:
            for indice in self.indices:
                buffer = pack(FORMAT_INDICE_PRIMARIO, *indice)
                saida.write(buffer)

    def extrai_arquivo(self, nome_entrada: str) -> None:
        '''Extrai os dados de um arquivo binário e adiciona no indice'''
        with open(nome_entrada, 'rb') as entrada:
            buffer = entrada.read(TAM_FORMAT_INDICE_PRIMARIO)
            while buffer != b'':
                unpacked = unpack(FORMAT_INDICE_PRIMARIO, buffer)
                self.adiciona_elemento(unpacked)
                buffer = entrada.read(TAM_FORMAT_INDICE_PRIMARIO)

    
class IndiceSecundario:

    indices: list[tuple[str, int]]#chave e prim_id
    lista_invertida: ListaInvertida

    def __init__(self, lista_invertida: ListaInvertida):
        self.indices = []
        self.lista_invertida = lista_invertida

    def adiciona_elemento(self, chave: str, id_elemento: int) -> None:
        '''Adiciona elemento no indice'''
        pos_chave = self.busca_chave(chave)
        
        if pos_chave is None:
            #não achou a chave, insere ordenado
            indices = self.indices
            indices.append((chave, id_elemento))
            
            i = len(indices) - 1
            pos_correta = False
            while i > 0 and not pos_correta:
                if indices[i] < indices[i-1]:
                    indices[i], indices[i-1] = indices[i-1], indices[i]
                else:
                    pos_correta = True
                i -= 1
            pos_chave = i
        
        self.lista_invertida.adiciona_elemento()

    
    def remove_elemento(self, chave: str) -> None:
        '''Remove um elemento pela chave'''
        raise NotImplementedError
    
    def busca_chave(self, chave: str) -> int | None:
        '''Retorna a posição da chave no indice. Se não encontrar, retorna None'''
    
class ListaInvertida:

    valores: list[tuple[int, int, int]]# id, prox_gen, prox_publi

    def __init__(self):
        self.valores = []

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
            #indice_sec_gen.adiciona_elemento(gen_registro, id_registro)
            #indice_sec_publi.adiciona_elemento(publi_regsitro, id_registro)

            tam_registro_bytes = dados.read(2)
            offset += 2 + tam_registro

    indice_pri.cria_arquivo("primario.ind")
    # cria_arquivo("primairo.ind", indice_pri.valores)
    # cria_arquivo("genero.ind", indice_sec_gen.valores)
    # cria_arquivo("publicadora.ind", indice_sec_publi.valores)
    # cria_arquivo("listaInvertida.lst", lista_invertida.valores)



def main() -> None:

    constroi_indices("games.dat")
    pri = IndicePrimario()
    pri.extrai_arquivo('primario.ind')
    
    with open("games.dat", 'rb') as entrada:
        for ind in pri.indices:
            entrada.seek(ind[1])
            tam = int.from_bytes(entrada.read(2), 'little')
            print(entrada.read(tam).decode().split('|'))
    
if __name__ == '__main__':
    main()