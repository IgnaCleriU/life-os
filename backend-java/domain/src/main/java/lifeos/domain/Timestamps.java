package lifeos.domain;

import java.time.Instant;
import java.time.temporal.ChronoUnit;

/** Reloj del dominio. */
final class Timestamps {

    private Timestamps() {}

    /**
     * Instante actual en UTC, truncado a microsegundos: es la resolución con la
     * que SQLite guarda las fechas, así una entidad recién creada es igual a la
     * misma entidad leída de la base.
     */
    static Instant now() {
        return Instant.now().truncatedTo(ChronoUnit.MICROS);
    }
}
