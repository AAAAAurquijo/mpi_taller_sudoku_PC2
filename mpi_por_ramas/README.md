# Tarea 2: repartir ramas de cada tablero

Implemención de versión por ramas MPI. Con `--all`, el proceso coordinador lee los 30 IDs de `seeds.txt` en orden. Para cada tablero, crea tareas a partir de opciones válidas de las primeras casillas vacías y reparte esas ramas entre procesos. Espera a que termine ese tablero antes de comenzar el siguiente: **los tableros se procesan secuencialmente y las ramas de cada tablero en paralelo**.

Cada proceso explora su rama con backtracking y comunica el resultado. Cuando se encuentra una solución, los demás deben dejar de buscar ese tablero. Muestra el estado y el tiempo parcial de cada ID al terminarlo, además del tiempo total de los 30. Conserva la opción `--id` para resolver un solo tablero.

Comandos para ejecutar `--id` y `--all` con el contenedor:

docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 13 python /app/mpi_por_ramas/ramas_mpi.py --id 7

docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 13 python /app/mpi_por_ramas/ramas_mpi.py --all
