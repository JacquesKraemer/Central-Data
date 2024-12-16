import requests
import pandas as pd
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import webbrowser

page_bg_gradient = """
<style>
[data-testid="stAppViewContainer"]{
    background: linear-gradient(to right, #eee8d5, #fdf6e3);
    color: black;
}
</style>
"""

# Insertar el CSS
st.markdown(page_bg_gradient, unsafe_allow_html=True)

# Título de la aplicación
st.markdown("<h1 style='text-align: center; color: black;'>Central Data</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Sobre el proyecto", "Principales varaibles", "Divisas"])

with tab1:
    st.markdown("""
    ##### ¿Cúal es el objetivo de esta aplicación?
    
    Cree esta pagina web para que los interesados en mantenerse actualizados sobre los datos economicos de nuestro país pudieran hacerlo facil y gratiutamente. Esta herramienta les permitirá explorar los **datos mas recientes** y la **evolución histórica** de las **principales variables económicas del Banco Central de la Republica Argentina**.
    
    ##### ¿Como funciona?

    Hacemos uso de la **API publica del BCRA**, un servicio de acceso a la información de esta intitución. Dado que este es un servicio relativamente nuevo, los datos historicos por lo general estan limitados en su disponibilidad a fechas relativamente recientes.
    Por ello, si un rango temporal que seleccionaron genera un error, lo mas probable es que este se deba a falta de datos en el servidor para la fecha seleccionada. Si se encuentran en esta situación, recomiendo que prueben intervalos temporales mas recientes. 
    Como regla general, hay datos disponibles a partir de diciembre del 2023, por lo que este suele ser un buen punto de partida. 
    """)

    st.write("Mas información sobre este servicio 👇")

    url = "https://www.bcra.gob.ar/BCRAyVos/catalogo-de-APIs-banco-central.asp"
    if st.button("APIs BCRA"):
        webbrowser.open_new_tab(url)
        

with tab2:

    # Subtítulo
    st.markdown("<h3 style='text-align: left;'>Principales variables</h3>", unsafe_allow_html=True)


    # Función para obtener las principales variables
    def principales_variables():
        try:
            # URL de la API
            url = "https://api.bcra.gob.ar/estadisticas/v2.0/principalesvariables"
            principales_variables = requests.get(url, verify=False)
            principales_variables.raise_for_status()

            # Extraer los datos relevantes
            data = principales_variables.json()
            relevant_data = data["results"]

            df_principales_variables = pd.DataFrame(relevant_data)
            df_principales_variables.drop('cdSerie', axis=1, inplace=True)
            df_principales_variables = df_principales_variables[df_principales_variables['idVariable'].isin([1,4,6,14,15,16,18,26,27,28,29,30,31])]

        except Exception as e:
            st.error(f"Error al obtener la información: {e}")

            df_principales_variables = pd.DataFrame()  # DataFrame vacío en caso de error
        
        return df_principales_variables

    # Llamar a la función y almacenar el DataFrame
    df_pv = principales_variables()

    # Mostrar el DataFrame si tiene datos
    if not df_pv.empty:
        columna_filtrar = 'descripcion'  # Reemplaza con el nombre de la columna que deseas usar

        if columna_filtrar in df_pv.columns:
            opciones = ["Todos"] + df_pv[columna_filtrar].unique().tolist()

            opcion_seleccionada = st.selectbox("Seleccione una variable para filtrar:",opciones)
            
            # Filtrar el DataFrame según la selección del usuario
            if opcion_seleccionada == "Todos":
                df_filtrado = df_pv  # Mostrar todos los datos
            else:
                df_filtrado = df_pv[df_pv[columna_filtrar] == opcion_seleccionada]

            st.dataframe(df_filtrado, use_container_width=True, hide_index=True, column_order=("idVariable", "fecha","descripcion","valor"))

        else:
            st.warning(f"La columna '{columna_filtrar}' no está disponible en el DataFrame.")
    else:
        st.warning("No hay datos disponibles para mostrar.")

    def Datos_historicos(idvariable, desde, hasta):
        try:
            # Formatear la URL
            url = f"https://api.bcra.gob.ar/estadisticas/v2.0/datosvariable/{idvariable}/{desde}/{hasta}"
            response = requests.get(url, verify=False)
            response.raise_for_status()

            # Procesar los datos
            data = response.json()
            relevant_data = data.get("results", [])
            df_Datos_historicos = pd.DataFrame(relevant_data)

        except Exception as e:
            st.error(f"Error al obtener datos: {e}")
            df_Datos_historicos = pd.DataFrame()  # Retorna un DataFrame vacío en caso de error

        return df_Datos_historicos

    # Interfaz de usuario en Streamlit
    st.markdown("<h3 style='text-align: center;'>Visualización de datos historicos</h3>", unsafe_allow_html=True)

    # Entrada del usuario
    id = st.text_input("Introduce el ID de la variable:", value="1")
    st.write("*Pueden obtener el id de la variable deseada de la tabla anterior.")

    desde = st.date_input("Desde:", value=pd.to_datetime("2024-11-01"))
    hasta = st.date_input("Hasta:", value=pd.to_datetime("2024-12-01"))
    st.write("*La disponibilidad de los datos en las fechas solicitadas depende del banco central.")

    # Convertir las fechas a formato string para la API
    desde_str = desde.strftime("%Y-%m-%d")
    hasta_str = hasta.strftime("%Y-%m-%d")

    # Botón para obtener los datos y generar el gráfico
    if st.button("Generar gráfico"):
        df_dh = Datos_historicos(id, desde_str, hasta_str)

        #- Buscamos la descripcion de la variable seleccionada:
        id_int = int(id)
        df_pv_filtrado = df_pv[df_pv['idVariable'] == id_int]

        valor_descripcion = df_pv_filtrado["descripcion"].iloc[0]

        if not df_dh.empty:
            # Eliminar columnas no relevantes
            if "idVariable" in df_dh.columns:
                df_dh.drop("idVariable", axis=1, inplace=True)

            # Generar gráfico con Plotly Express
            fig_pv = px.line(df_dh, x="fecha", y="valor", markers=True, title=f"{valor_descripcion}")
            fig_pv.update_layout(
                title={"text": f"{valor_descripcion} <br><sub>{desde} a {hasta}</sub>",
                    })
            
            st.plotly_chart(fig_pv)
        else:
            st.warning("No se encontraron datos para los parámetros ingresados. Pruebe modificando las fechas seleccionadas", icon="⚠️")
with tab3:
    
    st.markdown("<h3 style='text-align: left;'>Divisas</h3>", unsafe_allow_html=True)

    def obtener_cotizaciones(moneda, fecha_desde, fecha_hasta):
        base_url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/"
        url =f"{base_url}{moneda}?fechadesde={fecha_desde}&fechahasta={fecha_hasta}"

        date = []
        moneda = []
        cotizaciones = []

        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()

            data = response.json()
            
            if data['status'] == 200:
                results = data["results"]
                
                for i, cotizacion in enumerate(results):

                    fecha = cotizacion["fecha"]

                    detalle = cotizacion["detalle"][0]
                    codigo_moneda = detalle["codigoMoneda"]
                    tipoCotizacion = detalle["tipoCotizacion"]
                    
                    date.append(fecha)
                    moneda.append(codigo_moneda)
                    cotizaciones.append(tipoCotizacion)
            else:
                st.warning("No se encontraron cotizaciones para la fecha proporcionada.")

            df_cotizaciones = pd.DataFrame({
                "Fecha":date,
                "Moneda": moneda,
                "Cotización": cotizaciones
            })

            return df_cotizaciones 
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")

    # Detallar codigo de moneda, fecha desde y fecha hasta.
    url_master = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Maestros/Divisas"
    divisas = requests.get(url_master, verify=False)
    div_data = divisas.json()
    div_list = div_data["results"]

    df = pd.DataFrame(div_list)
    codigos = df["codigo"]

    cod_divisa = st.selectbox("Seleccione una variable para filtrar:", codigos)
    desde = st.date_input("Desde:", value=pd.to_datetime("2020-01-01"))
    hasta = st.date_input("Hasta:", value=pd.to_datetime("2024-12-10"))

    desde_str = desde.strftime("%Y-%m-%d")
    hasta_str = hasta.strftime("%Y-%m-%d")
    
    if st.button("Dolar oficial"):
        df_ch = obtener_cotizaciones(cod_divisa, desde_str, hasta_str)

        fig_pv = px.line(df_ch, x="Fecha", y="Cotización", title=f"Evolución del tipo de cambio oficial (USD)")
        fig_pv.update_layout(
            title={"text": f"Evolución del tipo de cambio oficial ({cod_divisa}) <br><sub>{desde} a {hasta}</sub>"})

        st.plotly_chart(fig_pv)    

st.divider()
st.markdown("<footer style='text-align: center;'>Creado por Jacques Kraemer - 2024</footer>", unsafe_allow_html=True)
