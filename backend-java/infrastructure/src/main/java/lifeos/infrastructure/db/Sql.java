package lifeos.infrastructure.db;

import java.util.Collections;

/** Fragmentos SQL compartidos por los repositorios. */
final class Sql {

    private Sql() {}

    /**
     * {@code AND column IN (?, ...)}. Con una lista vacía no matchea nada, igual
     * que {@code in_([])} en SQLAlchemy: una lista vacía no es "sin filtro".
     */
    static String in(String column, int size) {
        if (size == 0) {
            return " AND 1 = 0";
        }
        return " AND " + column + " IN (" + String.join(", ", Collections.nCopies(size, "?")) + ")";
    }
}
