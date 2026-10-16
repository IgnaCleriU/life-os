package lifeos.infrastructure.db;

import java.nio.file.Path;
import javax.sql.DataSource;
import org.springframework.jdbc.core.simple.JdbcClient;

/** Base SQLite en archivo temporal, con el esquema creado: nunca la base real. */
final class TestDatabase {

    final DataSource dataSource;
    final JdbcClient jdbc;

    TestDatabase(Path dir) {
        this.dataSource = SqliteDatabase.open("jdbc:sqlite:" + dir.resolve("test.db"));
        SqliteDatabase.createSchema(dataSource);
        this.jdbc = JdbcClient.create(dataSource);
    }

    SqliteProjectRepository projects() {
        return new SqliteProjectRepository(jdbc);
    }

    SqliteTaskRepository tasks() {
        return new SqliteTaskRepository(jdbc);
    }
}
