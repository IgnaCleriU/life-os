package lifeos.adapters.rest;

/** El request no tiene la forma esperada (campo faltante, tipo o valor inválido) → 422. */
public class RequestValidationException extends RuntimeException {

    public RequestValidationException(String message) {
        super(message);
    }
}
