package lifeos.adapters.rest;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;

/** Guardarraíl: los tests REST nunca resuelven la base real del usuario. */
class DatabaseIsolationTest extends RestTestSupport {

    @Value("${lifeos.database-url}")
    String databaseUrl;

    @Test
    void testsUseATemporaryDatabase() {
        String realDb = Path.of(System.getProperty("user.home"), ".local/share/life-os/lifeos.db").toString();

        assertThat(databaseUrl).startsWith("jdbc:sqlite:" + System.getProperty("java.io.tmpdir"));
        assertThat(databaseUrl).doesNotContain(realDb);
    }
}
