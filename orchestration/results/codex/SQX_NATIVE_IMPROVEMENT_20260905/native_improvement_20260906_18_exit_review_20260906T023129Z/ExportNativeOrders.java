import java.io.*;
import java.util.*;
import java.util.zip.*;
import com.strategyquant.tradinglib.*;

/** Reads exactly one orders.bin from an SQX archive using SQX's installed library. */
public class ExportNativeOrders {
    public static void main(String[] args) throws Exception {
        try (ZipFile z = new ZipFile(args[0])) {
            List<? extends ZipEntry> entries = Collections.list(z.entries()).stream()
                .filter(e -> e.getName().equals("orders.bin") || e.getName().endsWith("/orders.bin"))
                .toList();
            if (entries.size() != 1) throw new IOException("Exactly one native order stream required");
            try (ObjectInputStream in = new ObjectInputStream(z.getInputStream(entries.get(0)));
                 PrintWriter out = new PrintWriter(args[1], "UTF-8")) {
                OrdersList rows = new OrdersList("evidence");
                rows.readExternal(in);
                out.println("ticket,type,sample,open_time,close_time,size,pl,commission_swap,commission_applied,mae,mfe,balance,is_balance,is_canceled,is_pending,open_price,close_price,is_long,is_short,slippage_money,bars_in_trade,close_type,stop_loss,take_profit,exit_index");
                for (int i = 0; i < rows.size(); i++) {
                    Order o = rows.get(i);
                    out.printf(Locale.ROOT, "%d,%d,%d,%d,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%d,%d,%s,%s,%d%n",
                        o.Ticket, o.Type, o.SampleType, o.OpenTime, o.CloseTime, o.Size, o.PL,
                        o.CommSwap, o.CommSwapApplied, o.MAE, o.MFE, o.AccountBalance,
                        o.isBalanceOrder(), o.isCanceledOrder(), o.isPendingOrder(),
                        o.OpenPrice, o.ClosePrice, o.isLong(), o.isShort(), o.SlippageInMoney,
                        o.BarsInTrade, o.CloseType, o.StopLoss, o.TakeProfit, o.ExitIndex);
                }
                if (out.checkError()) throw new IOException("Incomplete orders export");
                System.out.println("Exported records=" + rows.size());
            }
        }
    }
}
