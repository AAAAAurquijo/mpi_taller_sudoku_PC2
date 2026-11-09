"""MPI por tableros: El proceso 0 entrega un tablero completo a cada trabajador y, cada vez que uno
termina, le da el siguiente (reparto dinamico)"""

import argparse
import sys
from pathlib import Path

from mpi4py import MPI

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from sudoku import resolver_con_tiempo          
from baseline_secuencial import leer_seeds     

TAG_TAREA, TAG_RESULTADO, TAG_FIN = 1, 2, 3
#TAG_TAREA (id, tablero) ; TAG_RESULTADO (id, resuelto, segundos) ; TAG_FIN nada

def trabajador(comm):
    status = MPI.Status()
    while True:
        tarea = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
        if status.Get_tag() == TAG_FIN:
            break
        identificador, tablero = tarea
        resuelto, segundos = resolver_con_tiempo(tablero)
        comm.send((identificador, resuelto, segundos), dest=0, tag=TAG_RESULTADO)

def coordinador(comm, size, args):
    seeds = leer_seeds(args.archivo)
    pendientes = [args.id] if args.id else list(seeds) #!
    total_ids = len(pendientes)
    resultados = {}
    activos = 0

    inicio = MPI.Wtime()

    #reparticion: una tarea por trabajador
    for w in range(1, size):
        if pendientes:
            i = pendientes.pop(0)
            comm.send((i, seeds[i]), dest=w, tag=TAG_TAREA)
            activos += 1
        else:
            comm.send(None, dest=w, tag=TAG_FIN)

    #recibe resultados y da otro tablero al trabajador que quede libre
    status = MPI.Status()
    while activos > 0:
        i, resuelto, seg = comm.recv(source=MPI.ANY_SOURCE, tag=TAG_RESULTADO,
                                     status=status)
        w = status.Get_source()
        resultados[i] = (resuelto, seg)
        print(f"\nID: {i}")
        print("Resuelto" if resuelto else "Sin solución")
        print(f"Tiempo parcial: {seg:.6f} segundos", flush=True)
        if pendientes:
            j = pendientes.pop(0)
            comm.send((j, seeds[j]), dest=w, tag=TAG_TAREA)
        else:
            comm.send(None, dest=w, tag=TAG_FIN)
            activos -= 1

    total = MPI.Wtime() - inicio
    resueltos = sum(1 for ok, _ in resultados.values() if ok)
    print(f"\nProcesados {len(resultados)} de {total_ids} tableros "
          f"({resueltos} resueltos)")
    print(f"Tiempo total: {total:.6f} segundos")

def main():
    comm = MPI.COMM_WORLD
    rank, size = comm.Get_rank(), comm.Get_size()

    parser = argparse.ArgumentParser(description="Sudoku MPI por tableros.")
    parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--id", "--seed", dest="id")
    seleccion.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if size == 1:
        if rank == 0:
            print("Usa al menos 2 procesos (-n 2): uno coordina y los demás resuelven.")
    elif rank == 0:
        coordinador(comm, size, args)
    else:
        trabajador(comm)


if __name__ == "__main__":
    main()


# docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 13 python /app/mpi_por_tableros/tableros_mpi.py --all
