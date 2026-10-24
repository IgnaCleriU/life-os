package lifeos.infrastructure.config;

import java.nio.file.Path;
import java.util.Map;

/**
 * Dónde vive la base de datos compartida (ADR 0007).
 *
 * <p>Las URLs usan la misma forma que el backend Python ({@code sqlite:///ruta}),
 * así {@code DATABASE_URL} significa lo mismo para los dos. Las funciones
 * reciben el entorno y el home explícitos para poder testearlas sin tocar el
 * proceso.
 */
public final class DatabaseLocation {

    private static final String SQLALCHEMY_PREFIX = "sqlite:///";
    private static final String JDBC_PREFIX = "jdbc:sqlite:";

    private DatabaseLocation() {}

    /**
     * Base por defecto en el directorio de datos del usuario (spec XDG). Una ruta
     * relativa al cwd haría que cada cliente termine con su propia base según
     * desde dónde se lo lance.
     */
    public static String defaultDatabaseUrl(Map<String, String> env, Path home) {
        String xdg = env.get("XDG_DATA_HOME");
        Path dataHome = xdg == null || xdg.isEmpty() ? home.resolve(".local/share") : Path.of(xdg);
        return SQLALCHEMY_PREFIX + dataHome.resolve("life-os").resolve("lifeos.db");
    }

    /** {@code DATABASE_URL} si está definida; si no, la ruta por defecto. */
    public static String resolveDatabaseUrl(Map<String, String> env, Path home) {
        String override = env.get("DATABASE_URL");
        return override == null || override.isEmpty() ? defaultDatabaseUrl(env, home) : override;
    }

    /** Traduce una URL de SQLAlchemy a JDBC; una URL JDBC de SQLite pasa tal cual. */
    public static String toJdbcUrl(String url) {
        if (url.startsWith(JDBC_PREFIX)) {
            return url;
        }
        if (url.startsWith(SQLALCHEMY_PREFIX)) {
            return JDBC_PREFIX + url.substring(SQLALCHEMY_PREFIX.length());
        }
        throw new IllegalArgumentException("Solo se soporta SQLite, no: " + url);
    }
}
