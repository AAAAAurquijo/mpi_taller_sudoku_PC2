# Tarea 3: combinar tableros y ramas

Implementación de versión híbririda MPI en esta carpeta. Reparte los IDs entre grupos de procesos y permite que los procesos de cada grupo exploren ramas distintas del tablero asignado.

* Con N grupos de tamaño 1 es como el método por tableros
* Con un solo grupo de tamaño N es como el método por ramas

Comando para ejecutar la implementación con el contenedor. 

docker run --rm -v "${PWD}:/app" augustosalazar/slim-mpi:2 mpiexec --allow-run-as-root --use-hwthread-cpus --oversubscribe -n 13 python /app/mpi_hibrido/hibrido_mpi.py --all --grupo G
