package lifeos.infrastructure.config;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;

/**
 * La ruta por defecto <b>no</b> depende del directorio de trabajo: REST, MCP y la
 * TUI son procesos distintos lanzados desde cwd distintos, y deben terminar en el
 * mismo archivo que el backend Python (ADR 0007).
 */
class DatabaseLocationTest {

    private static final Path HOME = Path.of("/home/someone");

    @Test
    void usesXdgDataHomeWhenSet() {
        assertThat(DatabaseLocation.defaultDatabaseUrl(Map.of("XDG_DATA_HOME", "/custom/data"), HOME))
                .isEqualTo("sqlite:////custom/data/life-os/lifeos.db");
    }

    @Test
    void fallsBackToLocalShare() {
        assertThat(DatabaseLocation.defaultDatabaseUrl(Map.of(), HOME))
                .isEqualTo("sqlite:////home/someone/.local/share/life-os/lifeos.db");
    }

    @Test
    void emptyXdgDataHomeFallsBackToLocalShare() {
        assertThat(DatabaseLocation.defaultDatabaseUrl(Map.of("XDG_DATA_HOME", ""), HOME))
                .isEqualTo("sqlite:////home/someone/.local/share/life-os/lifeos.db");
    }

    @Test
    void databaseUrlEnvOverridesTheDefault() {
        var env = Map.of("DATABASE_URL", "sqlite:///./other.db", "XDG_DATA_HOME", "/custom/data");

        assertThat(DatabaseLocation.resolveDatabaseUrl(env, HOME)).isEqualTo("sqlite:///./other.db");
    }

    @Test
    void resolveUsesTheDefaultWithoutOverride() {
        assertThat(DatabaseLocation.resolveDatabaseUrl(Map.of("XDG_DATA_HOME", "/custom/data"), HOME))
                .isEqualTo("sqlite:////custom/data/life-os/lifeos.db");
    }

    @Test
    void translatesSqlalchemyUrlsToJdbc() {
        assertThat(DatabaseLocation.toJdbcUrl("sqlite:////abs/path/lifeos.db"))
                .isEqualTo("jdbc:sqlite:/abs/path/lifeos.db");
        assertThat(DatabaseLocation.toJdbcUrl("sqlite:///./rel.db")).isEqualTo("jdbc:sqlite:./rel.db");
        assertThat(DatabaseLocation.toJdbcUrl("jdbc:sqlite:/already.db"))
                .isEqualTo("jdbc:sqlite:/already.db");
    }

    @Test
    void rejectsNonSqliteUrls() {
        assertThatThrownBy(() -> DatabaseLocation.toJdbcUrl("postgresql://localhost/lifeos"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
