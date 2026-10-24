package lifeos.adapters.rest;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Path;
import java.util.Properties;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.sqlite.SQLiteDataSource;

/** Guardarraíl: los tests REST nunca resuelven la base real del usuario. */
class DatabaseIsolationTest extends RestTestSupport {

    @Value("${lifeos.database-url}")
    String databaseUrl;

    @Autowired
    DataSource dataSource;

    @Test
    void testsUseATemporaryDatabase() {
        String realDb = Path.of(System.getProperty("user.home"), ".local/share/life-os/lifeos.db").toString();

        assertThat(databaseUrl).startsWith("jdbc:sqlite:" + System.getProperty("java.io.tmpdir"));
        assertThat(databaseUrl).doesNotContain(realDb);
    }

    @Test
    void theDataSourceWasBuiltAgainstTheTemporaryDatabase() throws Exception {
        // La propiedad no alcanza: lo que importa es contra qué ruta se construyó el bean.
        assertThat(dataSource.unwrap(SQLiteDataSource.class).getUrl())
                .startsWith("jdbc:sqlite:" + System.getProperty("java.io.tmpdir"));
    }

    @Test
    void withoutAnOverrideTestsPointAtAnUnusablePath() throws Exception {
        // Un test que olvide el override tiene que fallar al arrancar, no caer en
        // la ruta por defecto (la base real) porque la propiedad quedó vacía.
        var defaults = new Properties();
        try (var in = getClass().getResourceAsStream("/config/application.properties")) {
            defaults.load(in);
        }

        assertThat(defaults.getProperty("lifeos.database-url")).startsWith("jdbc:sqlite:/proc/");
    }
}
