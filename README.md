# Sistema de Detección de Emociones en Tiempo Real

Este sistema detecta emociones humanas usando una webcam, mostrando el análisis junto a un emoji en una GUI moderna.

## Modelos disponibles
- FER
- DeepFace

## Requisitos

- Python 3.12
- Visual Studio 2022 con C++ Build Tools (para dlib y cmake). Instalamos las dependencias C++, para ello tendremos que descargar el instalador de Visual Studio 2022, que es la última versión por ahora. Nos dirigimos a “Community” y lo descargamos. Seleccionamos el ejecutable y después de un par de procesos podremos ver la siguiente ventanita. De esta vamos a bajar un poquito y elegimos “Desarrollo para escritorio con C++” y luego seleccionamos instalar. 
- Descargar e instalar Cmake desde: https://cmake.org/download/
- Librerías: ver `requirements.txt`

## Importante

- ejecutar en consola antes de instalar los requerimientos: pip3 install setuptools

## Instalación

```bash
git clone https://github.com/MaycolPGR-aduch/DetectorEmociones.git
cd DetectorEmociones
pip install -r requirements.txt
python IntegratedGUI.py
