# Informe de resultados

Completa este informe después de implementar las tres tareas MPI. Ejecuta las comparaciones con el mismo archivo `seeds.txt`, en el mismo equipo y con el contenedor del taller.

## Entorno

- Equipo: ASUS TUF GAMING F15 con procesador 12th Gen Intel(R) Core(TM) i5-12500H (2.50 GHz)
- Versión del contenedor: augustosalazar/slim-mpi:2 / Docker version 29.9.2, build a82e528 
- Cantidad de repeticiones por medición: 3
- Valor común de `N` elegido: 13

## Comparación final con el mismo `N`

Repite tres veces cada ejecución y registra la mediana. Mantén fijo el `N` elegido en todas las filas MPI. Incluye `--allow-run-as-root --use-hwthread-cpus --oversubscribe` en `mpiexec`, igual que en la calibración, para permitir valores de `N` mayores que los slots detectados.

| Implementación | Caso | Procesos | Mediana del tiempo total (s) | Aceleración frente a secuencial |
| --- | --- | ---: | ---: | ---: |
| Secuencial | Todos los IDs | 1 | 93.677542 | 1,00 |
| MPI por tableros | Todos los IDs | 13 | 14.656790 | 6,391409 |
| MPI por ramas | Todos los IDs, uno después de otro | 13 | 35.211959 | 2,660389 |
| MPI híbrido | Todos los IDs | 13 | 17.402984 | 5,382543 |

Calcula la aceleración como `tiempo secuencial / tiempo MPI`. Mide el tiempo MPI desde el inicio del reparto hasta recibir todos los resultados necesarios.

## Conclusiones

- ¿Qué estrategia obtuvo el menor tiempo para los 30 tableros? ¿Cuánto mejoró respecto a la versión secuencial?

R/ La estrategia con menor tiempo para los 30 tableros fue MPI por tableros, fue aproximadamente 6,4 veces màs ràpida que la secuencial. 

- ¿Cómo afectaron la comunicación y las diferencias de duración entre tableros?

R/ En el mètodo de MPI por tableros el reparto dinámico evita que los procesos esperen a los tableros lentos. Esto explica el buen resultado Lo que lo limita es que el tablero más lento fija un piso al tiempo total, y que el coordinador no resuelve. En cambio, en el mètodo de MPI por ramas, por cada tablero se espera a que todos los trabajadores contesten antes de pasar al siguiente. Con el backtracking, una rama se puede resolver muy rápido o muy lento, esta desigualdad puede dejar a unos trabajadores esperando a otros.

- ¿Cómo se comparó repartir tableros con resolverlos en orden y repartir las ramas de cada uno?

R/ El híbrido queda en un intermedio, como reparte tableros entre grupos, da el buen rendimiento de tableros, pero dentro de cada grupo el costo de coordinar ramas pesa más que lo que gana al repartirlas.

* Para el método híbrido, explica cómo elegiste el tamaño de los grupos
Para elegir el tamaño de grupo, medí --all con cada número entre 2 y 12, hice tres repeticiones, saqué la mediana que obtuve como resultado de cada tamaño y seleccioné la de menor tiempo. Tuve en cuenta que: 
    * Con N grupos de tamaño 1 es como el método por tableros
    * Con un solo grupo de tamaño N es como el método por ramas
    Con grupos de tamaño diferente a 1, el que menor tiempo tardò fue el de tamaño 7, con una duraciòn de 21.051893 segundos