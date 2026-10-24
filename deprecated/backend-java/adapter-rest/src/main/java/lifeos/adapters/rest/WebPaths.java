package lifeos.adapters.rest;

import jakarta.servlet.http.HttpServletRequest;

/**
 * Qué rutas son la web estática ({@code /}, {@code /app}, {@code /app/**}).
 *
 * <p>Se decide sobre el URI crudo, sin decodificar, y falla cerrado: cualquier
 * cosa rara ({@code ..}, {@code ;}, {@code \}, {@code //}, otra
 * capitalización, un {@code %} mal formado o que codifica {@code / . \ ; % }
 * o un control) no cuenta como web y cae en la regla de la API, que exige
 * token. Los {@code %XX} comunes ({@code %20}, {@code %C3%B1}) sí valen: son
 * rutas legítimas del cliente. Así ninguna ruta de la API se alcanza sin token por parecer parte
 * de {@code /app}.
 */
final class WebPaths {

    private WebPaths() {}

    static boolean isWeb(HttpServletRequest request) {
        String uri = request.getRequestURI();
        String context = request.getContextPath();
        if (uri == null || !context.isEmpty()) {
            return false;
        }
        if (uri.equals("/") || uri.equals("/app")) {
            return true;
        }
        if (!uri.startsWith("/app/") || uri.contains("//") || hasDangerousEscape(uri)
                || uri.indexOf(';') >= 0 || uri.indexOf('\\') >= 0) {
            return false;
        }
        for (String segment : uri.split("/")) {
            if (segment.equals(".") || segment.equals("..")) {
                return false;
            }
        }
        return true;
    }

    /** {@code %} mal formado, o que codifica {@code / . \ ; %}, un control o DEL. */
    private static boolean hasDangerousEscape(String uri) {
        for (int i = uri.indexOf('%'); i >= 0; i = uri.indexOf('%', i + 1)) {
            if (i + 3 > uri.length()) {
                return true;
            }
            int hi = Character.digit(uri.charAt(i + 1), 16);
            int lo = Character.digit(uri.charAt(i + 2), 16);
            if (hi < 0 || lo < 0) {
                return true;
            }
            int value = hi * 16 + lo;
            if (value < 0x20 || value == 0x7f || value == '/' || value == '.' || value == '\\'
                    || value == ';' || value == '%') {
                return true;
            }
        }
        return false;
    }
}
