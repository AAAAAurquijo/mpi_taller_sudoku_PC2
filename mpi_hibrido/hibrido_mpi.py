"""MPI híbrido (tableros entre grupos + ramas dentro de cada grupo)"""

import argparse
import sys
from pathlib import Path

from mpi4py import MPI

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "mpi_por_ramas"))
from baseline_secuencial import leer_seeds
from ramas_mpi import resolver_tablero, trabajador, TAG_FIN


def main():
    comm = MPI.COMM_WORLD
    rank, size = comm.Get_rank(), comm.Get_size()

    parser = argparse.ArgumentParser(description="Sudoku MPI híbrido.")
    parser.add_argument("--archivo", type=Path, default=RAIZ / "seeds.txt")
    parser.add_argument("--grupo", type=int, default=2, help="tamaño de cada grupo de procesos")
    parser.add_argument("--profundidad", type=int, default=3)
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--id", "--seed", dest="id")
    seleccion.add_argument("--all", action="store_true")
    args = parser.parse_args()

    g = max(1, min(args.grupo, size)) #esta linea para que el tamaño de grupo sea valido
    color = rank // g #asignacion de rank a un grupo
    sub = comm.Split(color, rank) #comunicador solo del grupo. agrupacion
    es_lider = sub.Get_rank() == 0
    num_grupos = (size + g - 1) // g 

    seeds = leer_seeds(args.archivo)
    ids = [args.id] if args.id else list(seeds)
    mis_ids = ids[color::num_grupos] #se reparten los tableros entre grupos (estatico)

    comm.Barrier() #para que todos arranquen juntos
    inicio = MPI.Wtime()

    locales = []
    if es_lider:
        for i in mis_ids:
            t0 = MPI.Wtime()
            resuelto, _ = resolver_tablero(sub, seeds[i], args.profundidad)
            seg = MPI.Wtime() - t0
            locales.append((i, resuelto, seg))
            print(f"\nID: {i}  (grupo {color})")
            print("Resuelto" if resuelto else "Sin solución")
            print(f"Tiempo parcial: {seg:.6f} segundos", flush=True)
        for w in range(1, sub.Get_size()):
            sub.send(None, dest=w, tag=TAG_FIN)
    else:
        trabajador(sub)

    todos = comm.gather(locales, root=0) #se reúnen a los lideres (los resultados con una colectiva (gather))
    if rank == 0:
        total = MPI.Wtime() - inicio
        resultados = [r for lista in todos for r in lista]
        resueltos = sum(1 for _, ok, _ in resultados if ok)
        print(f"\nN={size}, grupos={num_grupos} de tamaño {g}")
        print(f"Procesados {len(resultados)} de {len(ids)} tableros "
              f"({resueltos} resueltos)")
        print(f"Tiempo total: {total:.6f} segundos")


if __name__ == "__main__":
    main()

# docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 13 python /app/mpi_hibrido/hibrido_mpi.py --all --grupo G
