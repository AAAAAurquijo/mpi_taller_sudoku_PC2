# Tarea 1: repartir tableros

Implementación de versión 1 MPI. Al ejecutar todos los tableros, cada ID es una tarea que se asigna a un proceso. Se reutiliza el resolvedor de `../sudoku.py` y reúne los estados en el proceso coordinador (con N procesos trabajan N-1).

Registra el tiempo total de ejecución y confirma que se procesaron los 30 IDs. 

Comando para ejecutar la implementación con el contenedor:

docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 13 python /app/mpi_por_tableros/tableros_mpi.py --all
