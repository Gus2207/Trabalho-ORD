from __future__ import annotations
from io import BufferedReader
from struct import pack, unpack

INDICE_DESCONHECIDO = -1

FORMAT_INDICE_PRIMARIO = 'HH'
TAM_FORMAT_INDICE_PRIMARIO = 4

FORMAT_INDICE_SECUNDARIO = '60si'
TAM_FORMAT_INDICE_SECUNDARIO = 64

FORMAT_LISTA_INVERTIDA = 'Hii'
TAM_FORMAT_LISTA_INVERTIDA = 12

class IndicePrimario:

    indices: list[tuple[int, int]]#id e offset

    def __init__(self):
        self.indices = []

    def busca_elemento_indice(self, id: int) -> int | None:
        '''Retorna o indice de um elemento na lista, baseado em seu id.
        Retorna None se não encotrar.'''
        for i in range(len(self.indices)) :
            if id == self.indices[i][0]:
                return i
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

    indices: list[tuple[str, int]]#chave e posicao_primeiro_list_inv
    lista_invertida: ListaInvertida
    col_prox_inv: int #Coluna de próximos elementos na lista invertida

    def __init__(self, lista_invertida: ListaInvertida, col_prox_inv: int):
        self.indices = []
        self.lista_invertida = lista_invertida
        self.col_prox_inv = col_prox_inv

    def canoniza_chave(self, chave: str) -> str:
        '''Retorna a chave em sua forma canônica do indice secundário'''
        return chave.replace(" ", "").upper()

    def busca_chave_indice(self, chave: str) -> int | None:
        '''Retorna a posição da chave no indice. Se não encontrar, retorna None'''
        canonica = self.canoniza_chave(chave)
        for i in range(len(self.indices)):
            if self.indices[i][0] == canonica:
                return i
        return None
    
    def adiciona_chave(self, chave_canonica: str) -> int:
        '''Adiciona uma chave que já esteja na forma canônica ao indice e retorna
        a sua posição. O primeiro elemento do encadeamento apontado é DESCONHECIDO (-1).'''
        indices = self.indices
        indices.append((chave_canonica, INDICE_DESCONHECIDO))
        
        i = len(indices) - 1
        pos_correta = False
        while i > 0 and not pos_correta:
            if indices[i] < indices[i-1]:
                indices[i], indices[i-1] = indices[i-1], indices[i]
                i -= 1
            else:
                pos_correta = True

        return i
    
    def adiciona_elemento(self, chave: str, id_elemento: int) -> None:
        '''Adiciona elemento no indice'''
        canonica = self.canoniza_chave(chave)
        pos_chave = self.busca_chave_indice(canonica)

        if pos_chave is None:
            pos_chave = self.adiciona_chave(canonica)
        
        # Adiciona elemento na lista invertida
        pos_inv = self.lista_invertida.busca_pos(id_elemento)
        if pos_inv is None:
            pos_inv = self.lista_invertida.adiciona_elemento(id_elemento)
            
        if self.indices[pos_chave][1] == INDICE_DESCONHECIDO:
            self.indices[pos_chave] = (canonica, pos_inv)
        
        else:
            pos_prim_elem = self.indices[pos_chave][1]
            prim_elem = self.lista_invertida.busca_elem(pos_prim_elem)
            if id_elemento < prim_elem[0]:
                self.lista_invertida.encadeia(pos_prim_elem, pos_inv, self.col_prox_inv)
                self.indices[pos_chave] = (canonica, pos_inv)
            
            else:
                self.lista_invertida.encadeia(pos_inv, pos_prim_elem, self.col_prox_inv)
    
    def remove_elemento(self, chave: str) -> None:
        '''Remove um elemento pela chave'''
        raise NotImplementedError
    
    def cria_arquivo(self, nome_saida: str) -> None:
        '''Cria um arquivo binário com os dados do indice'''
        with open(nome_saida, 'wb') as saida:
            for indice in self.indices:
                buffer = pack(FORMAT_INDICE_SECUNDARIO, indice[0].encode(), indice[1])
                saida.write(buffer)

    def extrai_arquivo(self, nome_entrada: str) -> None:
        '''Extrai os dados de um arquivo binário e adiciona no indice'''
        with open(nome_entrada, 'rb') as entrada:
            buffer = entrada.read(TAM_FORMAT_INDICE_SECUNDARIO)
            while buffer != b'':
                unpacked = unpack(FORMAT_INDICE_SECUNDARIO, buffer)
                indice = (unpacked[0].decode().strip('\x00'), unpacked[1])
                self.indices.append(indice)
                buffer = entrada.read(TAM_FORMAT_INDICE_SECUNDARIO)


class ListaInvertida:

    bindings: list[list[int]]# id, prox_gen, prox_publi

    def __init__(self):
        self.bindings = []

    def busca_elem(self, posicao: int) -> list[int]:
        '''Retorna o elemento na posição informada'''
        return self.bindings[posicao]
    
    def busca_pos(self, id: int) -> int | None:
        '''Retorna a posição do id na lista invertida.
        Retorna None se não encontrar.'''
        for i in range(len(self.bindings)):
            if self.bindings[i][0] == id:
                return i
        return None

    def adiciona_elemento(self, id_elemento: int) -> int:
        '''Adiciona elemento no indice baseado no id e retorna sua posição'''
        self.bindings.append([id_elemento, INDICE_DESCONHECIDO, INDICE_DESCONHECIDO])
        return len(self.bindings) - 1
    
    def remove_elemento(self, id: int) -> None:
        '''Remove um elemento pelo id'''
        raise NotImplementedError
    
    def encadeia(self, pos_novo_elem: int, pos_elem_base: int, col: int) -> None:
        '''Adiciona o elemento ao encadeamento da coluna'''
        novo_elem = self.bindings[pos_novo_elem]
        elem_base = self.bindings[pos_elem_base]
        pos_prox_elem = elem_base[col]
        prox_elem = self.bindings[pos_prox_elem]

        if pos_prox_elem is INDICE_DESCONHECIDO:
            elem_base[col] = pos_novo_elem
        elif novo_elem[0] < prox_elem[0]:
            novo_elem[col] = elem_base[col]
            elem_base[col] = pos_novo_elem

        elif novo_elem[0] > prox_elem[0]:
            if pos_prox_elem is INDICE_DESCONHECIDO:
                prox_elem[col] = pos_novo_elem
            else:
                self.encadeia(pos_novo_elem, pos_prox_elem, col)

    def cria_arquivo(self, nome_saida: str) -> None:
        '''Cria um arquivo binário com os dados da lista invertida'''
        with open(nome_saida, 'wb') as saida:
            for bind in self.bindings:
                buffer = pack(FORMAT_LISTA_INVERTIDA, *bind)
                saida.write(buffer)

    def extrai_arquivo(self, nome_entrada: str) -> None:
        '''Extrai os dados de um arquivo binário e adiciona na lista invertida'''
        with open(nome_entrada, 'rb') as entrada:
            buffer = entrada.read(TAM_FORMAT_LISTA_INVERTIDA)
            while buffer != b'':
                unpacked = unpack(FORMAT_LISTA_INVERTIDA, buffer)
                self.bindings.append(list(unpacked))
                buffer = entrada.read(TAM_FORMAT_LISTA_INVERTIDA)



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
        indice_sec_gen = IndiceSecundario(lista_invertida, 1)
        indice_sec_publi = IndiceSecundario(lista_invertida, 2)
        
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

            indice_pri.adiciona_elemento((id_registro, offset))
            indice_sec_gen.adiciona_elemento(gen_registro, id_registro)
            indice_sec_publi.adiciona_elemento(publi_regsitro, id_registro)

            tam_registro_bytes = dados.read(2)
            offset += 2 + tam_registro

    indice_pri.cria_arquivo("primario.ind")
    indice_sec_gen.cria_arquivo("genero.ind")
    indice_sec_publi.cria_arquivo("publicadora.ind")
    lista_invertida.cria_arquivo("listaInvertida.lst")



def main() -> None:

    constroi_indices("games.dat")
    lst_inv = ListaInvertida()
    lst_inv.extrai_arquivo('listaInvertida.lst')
    
    with open("games.dat", 'rb') as entrada:
        for ind in lst_inv.bindings:
            print(ind)
    
if __name__ == '__main__':
    main()