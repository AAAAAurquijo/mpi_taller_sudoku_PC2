"""MPI por ramas: Para cada tablero el coordinador genera ramas (combinaciones válidas de las primeras casillas
vacías) y las reparte entre los trabajadores. Cuando alguno encuentra la solución, los demás cancelan la búsqueda de ese tablero"""

import argparse
import sys
from pathlib import Path

from mpi4py import MPI

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from sudoku import puede_colocar, resolver      
from baseline_secuencial import leer_seeds      

TAG_TAREA, TAG_RESULTADO, TAG_STOP, TAG_FIN = 1, 2, 3, 4
REVISAR_CADA = 5000 #cada cuantos nodos el trabajador mira si hay un TAG_STOP


class Cancelado(Exception):
    """cuando el coordinador pide dejar de buscar TAG_STOP"""


def generar_ramas(tablero, profundidad):
    #devuelve tableros parciales con profundidad casillas vacías rellenadas (controla cuantas casillas se expanden para crear ramas)
    if profundidad == 0:
        return [[f[:] for f in tablero]]
    for f in range(9):
        for c in range(9):
            if tablero[f][c] == 0:
                ramas = []
                for v in range(1, 10):
                    if puede_colocar(tablero, f, c, v):
                        tablero[f][c] = v
                        ramas += generar_ramas(tablero, profundidad - 1)
                        tablero[f][c] = 0
                return ramas
    return [[f[:] for f in tablero]]   #cuando no quedan casillas vacías

def resolver_cancelable(tablero, comm, estado):
    #backtracking igual a sudoku.resolver, pero revisa si llego un STOP"""
    estado["nodos"] += 1
    if estado["nodos"] % REVISAR_CADA == 0 and comm.Iprobe(source=0, tag=TAG_STOP):
        comm.recv(source=0, tag=TAG_STOP)
        raise Cancelado
    
    for fila in range(9):
        for columna in range(9):
            if tablero[fila][columna] != 0:
                continue
            for valor in range(1, 10):
                if puede_colocar(tablero, fila, columna, valor):
                    tablero[fila][columna] = valor
                    if resolver_cancelable(tablero, comm, estado):
                        return True
                    tablero[fila][columna] = 0
            return False
    return True

def trabajador(comm):
    status = MPI.Status()
    while True:
        mensaje = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
        etiqueta = status.Get_tag()
        if etiqueta == TAG_FIN:
            break
        if etiqueta == TAG_STOP:
            continue #parada que llego tarde, ya no tenia rama activa
        tablero = mensaje
        estado = {"nodos": 0}
        try:
            if resolver_cancelable(tablero, comm, estado):
                respuesta = ("ENCONTRADO", tablero)
            else:
                respuesta = ("SIN_SOLUCION", None)
        except Cancelado:
            respuesta = ("CANCELADO", None)
        comm.send(respuesta, dest=0, tag=TAG_RESULTADO)

def resolver_tablero(comm, tablero, profundidad):
    #lo llama el coordinador y devuelve (resuelto, solucion)
    size = comm.Get_size()
    if size == 1:                      
        copia = [f[:] for f in tablero]
        return resolver(copia), copia

    ramas = generar_ramas([f[:] for f in tablero], profundidad)
    siguiente = 0
    ocupados = set()
    solucion = None

    for w in range(1, size):
        if siguiente < len(ramas):
            comm.send(ramas[siguiente], dest=w, tag=TAG_TAREA)
            siguiente += 1
            ocupados.add(w)

    status = MPI.Status()
    while ocupados:
        respuesta, datos = comm.recv(source=MPI.ANY_SOURCE, tag=TAG_RESULTADO,
                                     status=status)
        w = status.Get_source()
        ocupados.discard(w)
        if respuesta == "ENCONTRADO" and solucion is None:
            solucion = datos
            for otro in ocupados:      #detener a los demas
                comm.send(None, dest=otro, tag=TAG_STOP)
        if solucion is None and siguiente < len(ramas):
            comm.send(ramas[siguiente], dest=w, tag=TAG_TAREA)
            siguiente += 1
            ocupados.add(w)

    return solucion is not None, solucion

def main():
    comm = MPI.COMM_WORLD
    rank, size = comm.Get_rank(), comm.Get_size()

    parser = argparse.ArgumentParser(description="Sudoku MPI por ramas.")
    parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
    parser.add_argument("--profundidad", type=int, default=3,
                        help="casillas vacías que se expanden para crear ramas")
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--id", "--seed", dest="id")
    seleccion.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if rank != 0:
        trabajador(comm)
        return

    seeds = leer_seeds(args.archivo)
    ids = [args.id] if args.id else list(seeds)
    inicio = MPI.Wtime()
    for i in ids:
        t0 = MPI.Wtime()
        resuelto, _ = resolver_tablero(comm, seeds[i], args.profundidad)
        seg = MPI.Wtime() - t0
        print(f"\nID: {i}")
        print("Resuelto" if resuelto else "Sin solución")
        etiqueta = "Tiempo" if args.id else "Tiempo parcial"
        print(f"{etiqueta}: {seg:.6f} segundos", flush=True)
    total = MPI.Wtime() - inicio
    for w in range(1, size):
        comm.send(None, dest=w, tag=TAG_FIN)
    if not args.id:
        print(f"\nTiempo total: {total:.6f} segundos")


if __name__ == "__main__":
    main()


#docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 13 python /app/mpi_por_ramas/ramas_mpi.py --all
