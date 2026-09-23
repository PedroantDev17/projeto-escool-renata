import type { VercelRequest, VercelResponse } from '@vercel/node';
import { getToken } from '@vercel/connect';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    let token = '';

    // Se estiver rodando localmente no seu PC (localhost)
    if (process.env.NODE_ENV === 'development') {
      // INSIRA SEU TOKEN REAL DO NGROK ENTRE AS ASPAS ABAIXO:
      token = "stk_6A6SvDFQgru61s7KIrCXpF"; 
    } else {
      // Se estiver rodando online na produção da Vercel (usa o conector oficial)
      // @ts-ignore
      token = await getToken(req as any, '://ngrok.com');
    }

    if (!token) {
      return res.status(400).json({ success: false, error: 'Token nao configurado no ambiente local' });
    }
    
    return res.status(200).json({ success: true, token });
  } catch (error: any) {
    return res.status(500).json({ 
      success: false, 
      error: 'Erro na sincronizacao do token',
      mensagem: error?.message || 'Erro de conexao OIDC'
    });
  }
}
