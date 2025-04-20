# Sistema de Detección de Emociones en Tiempo Real

Este sistema detecta emociones humanas usando una webcam, mostrando el análisis junto a un emoji en una GUI moderna.

## Modelos disponibles
- FER
- DeepFace

## Requisitos

- Python 3.12
- Visual Studio 2022 con C++ Build Tools (para dlib y cmake)
- Descargar e instalar Cmake desde: https://cmake.org/download/
- Librerías: ver `requirements.txt`

## Importante

- ejecutar en consola antes de instalar los requerimientos: pip3 install setuptools

## Instalación

```bash
git clone https://github.com/MaycolPGR-aduch/DetectorEmociones.git
cd DetectorEmociones
pip install -r requirements.txt
python GUI.py
