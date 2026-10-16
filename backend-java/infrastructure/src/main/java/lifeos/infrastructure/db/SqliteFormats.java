package lifeos.infrastructure.db;

import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeFormatterBuilder;
import java.time.temporal.ChronoField;

/**
 * Conversión entre tipos Java y el texto que SQLAlchemy guarda en SQLite.
 *
 * <p>Las fechas se pasan como strings y nunca por la conversión del driver:
 * sqlite-jdbc guardaría epoch millis, que Python no sabe leer y que rompen la
 * comparación {@code due_date <= ?}.
 */
final class SqliteFormats {

    /** Lo que escribe SQLAlchemy: naive UTC, separador espacio, siempre 6 decimales. */
    private static final DateTimeFormatter WRITE =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSSSSS");

    /** Al leer se tolera la fracción ausente o más corta. */
    private static final DateTimeFormatter READ = new DateTimeFormatterBuilder()
            .appendPattern("yyyy-MM-dd HH:mm:ss")
            .optionalStart()
            .appendFraction(ChronoField.NANO_OF_SECOND, 0, 9, true)
            .optionalEnd()
            .toFormatter();

    private SqliteFormats() {}

    static String instant(Instant value) {
        return value == null ? null : WRITE.format(LocalDateTime.ofInstant(value, ZoneOffset.UTC));
    }

    static Instant instant(String value) {
        return value == null ? null : LocalDateTime.parse(value, READ).toInstant(ZoneOffset.UTC);
    }

    static String date(LocalDate value) {
        return value == null ? null : value.toString();
    }

    static LocalDate date(String value) {
        return value == null ? null : LocalDate.parse(value);
    }
}
