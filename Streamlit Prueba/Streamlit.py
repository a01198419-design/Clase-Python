import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

# Ignorar advertencias comunes de pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- Configuración de la Página ---
st.set_page_config(layout="wide", page_title="Dashboard de Ventas")

# --- Define el nombre de tu archivo ---
NOMBRE_DEL_ARCHIVO_CSV = "vendedores.csv"

# --- Carga de Datos ---
@st.cache_data
def load_data(file_name):
    try:
        # Lee el archivo CSV
        df = pd.read_csv(file_name)
        
        # --- MODIFICACIÓN IMPORTANTE ---
        # Combinamos NOMBRE y APELLIDO para crear la columna 'Vendedor'
        if 'NOMBRE' in df.columns and 'APELLIDO' in df.columns:
            df['Vendedor'] = df['NOMBRE'] + ' ' + df['APELLIDO']
        else:
            st.error("El archivo CSV debe tener las columnas 'NOMBRE' y 'APELLIDO'.")
            return None
        # --- Fin de la modificación ---

        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{file_name}' en la carpeta.")
        st.info(f"Por favor, asegúrate de que '{file_name}' esté en la misma carpeta que 'Streamlit.py'.")
        return None
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo: {e}")
        return None

df_ventas = load_data(NOMBRE_DEL_ARCHIVO_CSV)

# Si los datos no se cargaron, detenemos la ejecución
if df_ventas is None:
    st.stop()

# --- Título del Dashboard ---
st.title("📊 Dashboard de Desempeño de Vendedores")
st.markdown("---")

# --- Columnas correctas (basadas en tu archivo) ---
COLUMNA_REGION = 'REGION'
COLUMNA_VENTAS = 'VENTAS TOTALES'
COLUMNA_UNIDADES = 'UNIDADES VENDIDAS'
COLUMNA_VENDEDOR = 'Vendedor' # Esta la creamos nosotros

# --- Barra Lateral (Sidebar) de Filtros ---
st.sidebar.header("Filtros Globales")

try:
    regiones_disponibles = sorted(df_ventas[COLUMNA_REGION].unique())
    region_seleccionada = st.sidebar.multiselect(
        "Selecciona Región:",
        options=regiones_disponibles,
        default=regiones_disponibles  # Por defecto, todas están seleccionadas
    )

    # Filtrar el DataFrame principal basado en la selección
    if not region_seleccionada:
        st.sidebar.warning("Por favor, selecciona al menos una región.")
        df_filtrado = pd.DataFrame(columns=df_ventas.columns)
    else:
        df_filtrado = df_ventas[df_ventas[COLUMNA_REGION].isin(region_seleccionada)]

except KeyError:
    st.error(f"Error: La columna '{COLUMNA_REGION}' no se encontró en el archivo CSV.")
    st.stop()
except Exception as e:
    st.error(f"Un error inesperado ocurrió con el filtro de región: {e}")
    st.stop()


# --- Cuerpo Principal del Dashboard ---

if df_filtrado.empty:
    st.warning("No hay datos para mostrar con los filtros seleccionados.")
else:
    try:
        # --- KPIs Principales (Métricas) ---
        st.header("Resumen General (Filtrado)")
        
        total_ventas = float(df_filtrado[COLUMNA_VENTAS].sum())
        total_unidades = int(df_filtrado[COLUMNA_UNIDADES].sum())
        
        col_kpi1, col_kpi2 = st.columns(2)
        with col_kpi1:
            st.metric(label="Ventas Totales", value=f"${total_ventas:,.2f}")
        with col_kpi2:
            st.metric(label="Unidades Vendidas", value=f"{total_unidades:,.0f}")

        st.markdown("---")

        # --- Sección de Gráficas ---
        st.header("Análisis Gráfico por Vendedor")

        df_agrupado = df_filtrado.groupby(COLUMNA_VENDEDOR).agg({
            COLUMNA_UNIDADES: 'sum',
            COLUMNA_VENTAS: 'sum'
        }).reset_index()

        # Calcular porcentaje de ventas (basado en el total filtrado)
        total_ventas_filtrado = df_agrupado[COLUMNA_VENTAS].sum()
        if total_ventas_filtrado > 0:
            df_agrupado['Porcentaje Ventas'] = (df_agrupado[COLUMNA_VENTAS] / total_ventas_filtrado)
        else:
            df_agrupado['Porcentaje Ventas'] = 0


        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("Unidades Vendidas")
            fig_unidades = px.bar(
                df_agrupado.sort_values(COLUMNA_UNIDADES, ascending=False),
                x=COLUMNA_VENDEDOR,
                y=COLUMNA_UNIDADES,
                title='Unidades Vendidas por Vendedor',
                color=COLUMNA_VENDEDOR,
                template='plotly_white'
            )
            st.plotly_chart(fig_unidades, use_container_width=True)

        with col_graf2:
            st.subheader("Ventas Totales")
            fig_ventas = px.bar(
                df_agrupado.sort_values(COLUMNA_VENTAS, ascending=False),
                x=COLUMNA_VENDEDOR,
                y=COLUMNA_VENTAS,
                title='Ventas Totales ($) por Vendedor',
                color=COLUMNA_VENDEDOR,
                template='plotly_white'
            )
            fig_ventas.update_layout(yaxis_title="Ventas Totales ($)")
            st.plotly_chart(fig_ventas, use_container_width=True)
        
        st.subheader("Distribución de Ventas (%)")
        fig_pie = px.pie(
            df_agrupado,
            names=COLUMNA_VENDEDOR,
            values='Porcentaje Ventas',
            title='Porcentaje de Ventas por Vendedor',
            hole=0.3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        # --- Sección de Vendedor Específico ---
        st.header("Análisis por Vendedor Específico")

        vendedores_disponibles = sorted(df_filtrado[COLUMNA_VENDEDOR].unique())
        vendedor_seleccionado = st.selectbox(
            "Selecciona un Vendedor:",
            options=vendedores_disponibles
        )

        if vendedor_seleccionado:
            with st.container(border=True):
                st.subheader(f"Detalle de: {vendedor_seleccionado}")
                
                df_vendedor = df_filtrado[df_filtrado[COLUMNA_VENDEDOR] == vendedor_seleccionado]
                
                kpi_v_ventas = float(df_vendedor[COLUMNA_VENTAS].sum())
                kpi_v_unidades = int(df_vendedor[COLUMNA_UNIDADES].sum())
                kpi_v_region = ", ".join(df_vendedor[COLUMNA_REGION].unique())
                
                kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                kpi_col1.metric("Ventas Totales", f"${kpi_v_ventas:,.2f}")
                kpi_col2.metric("Unidades Vendidas", f"{kpi_v_unidades:,.0f}")
                kpi_col3.metric("Regiones Asignadas", kpi_v_region)
                
                # Mostramos la tabla del vendedor, eliminando columnas que ya usamos
                columnas_a_mostrar = [col for col in df_vendedor.columns if col not in ['NOMBRE', 'APELLIDO', 'Vendedor']]
                st.dataframe(df_vendedor[columnas_a_mostrar])

        st.markdown("---")

        # --- Sección de Datos Completos (en un expander) ---
        st.header("Datos Completos (Filtrados por Región)")
        with st.expander("Clic para ver la tabla de datos completa"):
            st.dataframe(df_filtrado)

    except KeyError as e:
        st.error(f"Error: Una columna clave como '{e.name}' no se encontró.")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los datos: {e}")