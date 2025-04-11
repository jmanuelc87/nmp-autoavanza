# Nacional Monte de Piedad Automatizacion con IA del Proyecto AutoAvanza

El objetivo principal es desarrollar una prueba de concepto de inteligencia artificial que permita automatizar el proceso de alta de documentos del producto AutoAvanza y otorgar mayor autonomía al cliente desde las plataformas digitales de Nacional Monte de Piedad. Esto permitirá generar una preoferta confiable de forma más rápida y efectiva, ayudando a cerrar la brecha entre la solicitud inicial y la formalización del crédito.


## Prueba de concepto

1. Toma de fotos
2. Carga a plataforma
3. Extracción de datos
4. Cotejo de información
5. Dictamen documental
6. Pre-oferta


## Estructura del Proyecto

La estructura del proyecto esta definida de la siguiente forma:

```
project_root/
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── notebooks/
└── src/
    ├── models/
    └── pipelines/
```

- En la carpeta `notebooks` se deben almacenar los documentos de colab o jupyter notebooks
- En la carpeta `data` se deben almacenar los datos con los cuales trabajaremos y tiene diferentes divisiones:
   - `bronze` estan los datos en crudo
   - `silver` estan los datos pre-procesados
   - `gold` estan los datos listos para consumo de un algoritmo de ml
- En la carpeta `src/pipelines` se deben almacenar los scripts de python para ejecutar el entrenamiento o preprocesamiento de los datos
- En la carpeta `src/models` se deben almacenar los archivos de python que contienen las arquitecturas desarrolladas
