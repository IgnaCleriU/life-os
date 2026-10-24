package lifeos.application;

/**
 * Cambio opcional a un campo anulable en una actualización parcial.
 *
 * <p>Distingue "no tocar el campo" ({@link #unset()}) de "ponerlo en null"
 * ({@code Change.to(null)}), algo que un simple {@code null} no puede expresar.
 */
public final class Change<T> {

    private static final Change<?> UNSET = new Change<>(false, null);

    private final boolean set;
    private final T value;

    private Change(boolean set, T value) {
        this.set = set;
        this.value = value;
    }

    @SuppressWarnings("unchecked")
    public static <T> Change<T> unset() {
        return (Change<T>) UNSET;
    }

    public static <T> Change<T> to(T value) {
        return new Change<>(true, value);
    }

    public boolean isSet() {
        return set;
    }

    /** Valor nuevo (puede ser null); solo tiene sentido si {@link #isSet()}. */
    public T value() {
        return value;
    }
}
