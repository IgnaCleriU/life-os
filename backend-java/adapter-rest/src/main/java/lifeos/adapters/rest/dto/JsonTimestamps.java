package lifeos.adapters.rest.dto;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

/**
 * Instantes en el formato que usa Pydantic: ISO-8601 en UTC con "Z", seis
 * decimales si hay microsegundos y ninguno si no.
 */
final class JsonTimestamps {

    private static final DateTimeFormatter WITH_MICROS =
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'").withZone(ZoneOffset.UTC);
    private static final DateTimeFormatter WHOLE_SECONDS =
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'").withZone(ZoneOffset.UTC);

    private JsonTimestamps() {}

    static String format(Instant instant) {
        return (instant.getNano() == 0 ? WHOLE_SECONDS : WITH_MICROS).format(instant);
    }
}
